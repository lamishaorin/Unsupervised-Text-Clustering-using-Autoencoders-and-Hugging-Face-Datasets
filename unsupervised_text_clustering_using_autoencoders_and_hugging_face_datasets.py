# -*- coding: utf-8 -*-
"""Unsupervised Text Clustering using  Autoencoders and Hugging Face Datasets

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1SeZ1BPxme_VVLp7wkqr_3H0XpszyKE6R
"""

import torch
import torch .nn as nn
import torch . optim as optim
from torch . utils . data import DataLoader
import torchvision . transforms as transforms
import torchvision . datasets as datasets

!pip install datasets

!pip install pandas

import pandas as pd

url = "hf://datasets/Zhouhc/attack-agnews/agnews_train.csv"
df = pd.read_csv(url)

# Display the first few rows of the dataset
print(df.head())

df.head()        # Shows the first 5 rows
df.head(10)      # Shows the first 10 rows

# Use last 10% of dataset
df_last10 = df.tail(int(0.1 * len(df)))
texts = df_last10['text'].tolist()

from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts, batch_size=16, show_progress_bar=True)

import torch
from torch.utils.data import Dataset

class TextDataset(Dataset):
    def __init__(self, embeddings):
        self.embeddings = torch.tensor(embeddings, dtype=torch.float32)

    def __len__(self):
        return len(self.embeddings)

    def __getitem__(self, idx):
        return self.embeddings[idx]

import torch.nn as nn

class Autoencoder(nn.Module):
    def __init__(self, input_dim=384, hidden_dim=128, latent_dim=64):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x):
        z = self.encoder(x)
        x_recon = self.decoder(z)
        return x_recon, z

from torch.utils.data import DataLoader
import torch.optim as optim

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Prepare data
dataset = TextDataset(embeddings)
dataloader = DataLoader(dataset, batch_size=8, shuffle=True)

# Initialize model
model = Autoencoder().to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)

# Train
epochs = 10
for epoch in range(epochs):
    model.train()
    total_loss = 0
    for batch in dataloader:
        batch = batch.to(device)
        recon, _ = model(batch)
        loss = criterion(recon, batch)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss:.4f}")

model.eval()
latent_vectors = []
with torch.no_grad():
    for batch in dataloader:
        batch = batch.to(device)
        _, z = model(batch)
        latent_vectors.append(z.cpu())
latent_vectors = torch.cat(latent_vectors).numpy()

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

kmeans = KMeans(n_clusters=4, random_state=42)
labels = kmeans.fit_predict(latent_vectors)

silhouette = silhouette_score(latent_vectors, labels)
db_score = davies_bouldin_score(latent_vectors, labels)
ch_score = calinski_harabasz_score(latent_vectors, labels)

print(f"Silhouette Score: {silhouette:.4f}")
print(f"Davies-Bouldin Index: {db_score:.4f}")
print(f"Calinski-Harabasz Index: {ch_score:.4f}")

from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

tsne = TSNE(n_components=2, perplexity=30, random_state=42)
reduced = tsne.fit_transform(latent_vectors)

plt.figure(figsize=(8, 6))
plt.scatter(reduced[:, 0], reduced[:, 1], c=labels, cmap='tab10', alpha=0.7)
plt.title("t-SNE Clustering of News Embeddings")
plt.xlabel("Component 1")
plt.ylabel("Component 2")
plt.colorbar(label="Cluster")
plt.grid(True)
plt.show()