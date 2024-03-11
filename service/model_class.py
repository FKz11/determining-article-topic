import torch
import torch.nn as nn
import numpy as np


class Model_hubs(nn.Module):
    def __init__(self, size_in, size_hide, size_out):
        super().__init__()
        self.linear_1 = nn.Linear(size_in, size_hide)
        self.bn = nn.BatchNorm1d(size_hide)
        self.tanh = nn.Tanh()
        self.dp = nn.Dropout(0.8)
        self.linear_2 = nn.Linear(size_hide, size_out)

    def forward(self, x):
        x = x.to(torch.float32)
        x = self.linear_1(x)
        x = self.bn(x)
        x = self.tanh(x)
        x = self.dp(x)
        x = self.linear_2(x)
        return x

    def predict(self, text, del_puncts, get_tokens, tfidf_vectorizer, id2hub, k=5, device='cpu'):
        clear_text = del_puncts(text)
        tokens_text = get_tokens(clear_text)
        tfidf_vector = tfidf_vectorizer.transform([tokens_text]).toarray()[0]
        output = self.forward(torch.tensor(np.array([tfidf_vector])).to(device)).detach().cpu().numpy()[0]
        preds = np.argsort(output)[::-1][:k]
        scores = output[preds]
        hubs = [id2hub[id_hub] for id_hub in preds]
        return list(zip(hubs, scores))
