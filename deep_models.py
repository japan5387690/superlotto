#!/usr/bin/env python3
"""深度學習預測模型：LSTM 與 Transformer。

把威力彩當「時間序列」丟給神經網路，看它能不能從過去 L 期的開獎
學出「下一期會開哪些號」。每期編碼成 46 維 multi-hot 向量
(第一區 1-38 → 38 維 + 第二區 1-8 → 8 維)。

模型輸入：過去 SEQ_LEN 期的向量序列
模型輸出：第一區 38 個號碼的機率 + 第二區 8 個號碼的機率
取號：第一區取機率最高 6 個、第二區取最高 1 個。

★ 重點（誠實揭露）：樂透是獨立隨機事件，理論上序列裡沒有可學的結構。
這些模型存在的目的，是用「真的把最強的深度學習丟下去」的實證，
證明它的命中率依然只會貼著隨機亂猜線。請對照 backtest_deep.json。
"""
import numpy as np
import torch
import torch.nn as nn

ZONE1_MAX = 38
ZONE2_MAX = 8
SEQ_LEN = 20            # 用過去 20 期預測下一期
VEC_DIM = ZONE1_MAX + ZONE2_MAX  # 46

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def draw_to_vec(d):
    """單期開獎 → 46 維 multi-hot 向量 (numpy float32)。"""
    v = np.zeros(VEC_DIM, dtype=np.float32)
    for n in d["zone1"]:
        v[n - 1] = 1.0
    v[ZONE1_MAX + d["zone2"] - 1] = 1.0
    return v


def build_sequences(draws, seq_len=SEQ_LEN):
    """把開獎序列切成 (X, y1, y2) 監督式樣本。

    X[i]  = 第 i..i+seq_len-1 期的向量序列 (seq_len, 46)
    y1[i] = 第 i+seq_len 期第一區 multi-hot (38,)
    y2[i] = 第 i+seq_len 期第二區號碼 index (0-7)
    """
    vecs = np.stack([draw_to_vec(d) for d in draws])
    X, Y1, Y2 = [], [], []
    for i in range(len(draws) - seq_len):
        X.append(vecs[i:i + seq_len])
        Y1.append(vecs[i + seq_len][:ZONE1_MAX])
        Y2.append(int(draws[i + seq_len]["zone2"]) - 1)
    if not X:
        return None
    return (
        torch.tensor(np.stack(X)),
        torch.tensor(np.stack(Y1)),
        torch.tensor(np.array(Y2), dtype=torch.long),
    )


class LSTMPredictor(nn.Module):
    """雙層 LSTM → 兩個輸出頭（第一區 38、第二區 8）。"""

    def __init__(self, hidden=128):
        super().__init__()
        self.lstm = nn.LSTM(VEC_DIM, hidden, num_layers=2,
                            batch_first=True, dropout=0.2)
        self.head1 = nn.Linear(hidden, ZONE1_MAX)
        self.head2 = nn.Linear(hidden, ZONE2_MAX)

    def forward(self, x):
        out, _ = self.lstm(x)
        h = out[:, -1, :]          # 取最後一步
        return self.head1(h), self.head2(h)


class TransformerPredictor(nn.Module):
    """Transformer Encoder → 池化 → 兩個輸出頭。"""

    def __init__(self, d_model=64, nhead=4, layers=2):
        super().__init__()
        self.proj = nn.Linear(VEC_DIM, d_model)
        self.pos = nn.Parameter(torch.randn(1, SEQ_LEN, d_model) * 0.02)
        enc = nn.TransformerEncoderLayer(
            d_model, nhead, dim_feedforward=d_model * 4,
            dropout=0.2, batch_first=True)
        self.enc = nn.TransformerEncoder(enc, layers)
        self.head1 = nn.Linear(d_model, ZONE1_MAX)
        self.head2 = nn.Linear(d_model, ZONE2_MAX)

    def forward(self, x):
        h = self.proj(x) + self.pos[:, :x.size(1), :]
        h = self.enc(h)
        h = h.mean(dim=1)          # 平均池化
        return self.head1(h), self.head2(h)


def train_model(model, draws, epochs=40, lr=1e-3, batch=64, seq_len=SEQ_LEN,
                verbose=False):
    """在 draws 上訓練模型。第一區用 multi-label BCE、第二區用 CrossEntropy。"""
    data = build_sequences(draws, seq_len)
    if data is None:
        return model
    X, Y1, Y2 = (t.to(DEVICE) for t in data)
    model = model.to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss()
    n = X.size(0)
    model.train()
    for ep in range(epochs):
        perm = torch.randperm(n, device=DEVICE)
        tot = 0.0
        for s in range(0, n, batch):
            idx = perm[s:s + batch]
            opt.zero_grad()
            o1, o2 = model(X[idx])
            loss = bce(o1, Y1[idx]) + ce(o2, Y2[idx])
            loss.backward()
            opt.step()
            tot += loss.item() * idx.size(0)
        if verbose and (ep + 1) % 10 == 0:
            print(f"  epoch {ep+1}/{epochs}  loss={tot/n:.4f}")
    return model


@torch.no_grad()
def predict(model, recent_draws, seq_len=SEQ_LEN):
    """用最近 seq_len 期預測下一期。回傳 {zone1:[6], zone2:int}。"""
    model = model.to(DEVICE).eval()
    window = recent_draws[-seq_len:]
    if len(window) < seq_len:        # 暖身不足，前面補零向量
        pad = [None] * (seq_len - len(window))
        vecs = [np.zeros(VEC_DIM, dtype=np.float32) for _ in pad] + \
               [draw_to_vec(d) for d in window]
    else:
        vecs = [draw_to_vec(d) for d in window]
    x = torch.tensor(np.stack(vecs)).unsqueeze(0).to(DEVICE)
    o1, o2 = model(x)
    p1 = torch.sigmoid(o1)[0].cpu().numpy()
    p2 = torch.softmax(o2, dim=1)[0].cpu().numpy()
    zone1 = sorted((np.argsort(p1)[-6:] + 1).tolist())
    zone2 = int(np.argmax(p2) + 1)
    return {"zone1": zone1, "zone2": zone2}


MODEL_FACTORY = {
    "lstm": lambda: LSTMPredictor(),
    "transformer": lambda: TransformerPredictor(),
}
DEEP_NAMES = {"lstm": "LSTM 神經網路", "transformer": "Transformer 神經網路"}
DEEP_DESC = {
    "lstm": "雙層 LSTM 時序模型，用過去 20 期序列學習下期號碼分布",
    "transformer": "Transformer 自注意力模型，用過去 20 期序列學習下期號碼分布",
}
