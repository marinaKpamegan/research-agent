# 🔍 Research Agent — RAG sur arXiv & données publiques françaises

> Agent de recherche intelligent combinant veille scientifique (arXiv) et données réglementaires françaises (data.gouv.fr) — réponses sourcées, hallucinations minimisées, pipeline RAG complet en production.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![LangChain](https://img.shields.io/badge/LangChain-0.2+-green?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-latest-purple?style=flat-square)
![FAISS](https://img.shields.io/badge/VectorStore-FAISS%20%2F%20Chroma-orange?style=flat-square)
![FastAPI](https://img.shields.io/badge/API-FastAPI-teal?style=flat-square)
![Docker](https://img.shields.io/badge/Deploy-Docker-blue?style=flat-square)

---

## 🎯 Problème résolu

Un chercheur ou analyste passe en moyenne **3h/semaine** à naviguer entre les papiers arXiv et les jeux de données publics français pour alimenter sa veille. Ce projet réduit ça à **quelques secondes** — l'agent interroge les deux sources, croise les informations et cite ses sources avec précision.

**Exemples de questions supportées :**

```
"Quelles sont les dernières avancées en RAG hybride publiées sur arXiv ?"
"Quels jeux de données publics français sont disponibles sur le thème de l'énergie ?"
"Donne-moi les papiers les plus récents sur les systèmes multi-agents LLM."
"Quelles données data.gouv.fr portent sur la santé publique en 2024 ?"
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Query                          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              LangGraph Orchestrator                     │
│   ┌──────────┐   ┌──────────┐   ┌──────────────────┐   │
│   │  Router  │──▶│ Retriever│──▶│  Re-ranker       │   │
│   │  Agent   │   │  Agent   │   │  + Grounding     │   │
│   └──────────┘   └──────────┘   └──────────────────┘   │
└──────────┬───────────────────────────────┬──────────────┘
           │                               │
           ▼                               ▼
┌──────────────────┐             ┌──────────────────────┐
│   arXiv Source   │             │  data.gouv.fr Source │
│                  │             │                      │
│ • 500+ papiers   │             │ • Jeux de données    │
│   cs.AI / cs.CL  │             │   publics français   │
│   cs.IR / cs.LG  │             │ • API CKAN           │
│ • PDF parsing    │             │ • Métadonnées JSON   │
│ • Abstracts +    │             │ • Mise à jour        │
│   métadonnées    │             │   périodique         │
└────────┬─────────┘             └──────────┬───────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────────────────────────────────────────────┐
│              Vector Store (FAISS / Chroma)              │
│         Embeddings dense — HuggingFace / OpenAI         │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            LLM Response + Source Citations              │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Fonctionnalités

- **Dual-source retrieval** — interroge arXiv et data.gouv.fr en parallèle et fusionne les résultats
- **Routing intelligent** — le LangGraph Router détecte la source la plus pertinente selon la question
- **Chunking sémantique** — découpe les documents aux frontières logiques, pas à la coupure arbitraire
- **Re-ranking** — les chunks récupérés sont re-classés par un cross-encoder avant d'aller au LLM
- **Grounding check** — chaque affirmation est vérifiée contre les sources pour détecter les hallucinations
- **Citations précises** — chaque réponse cite le titre, auteur, date et section du document source
- **Mémoire conversationnelle** — historique compressé pour des échanges multi-tours cohérents
- **API FastAPI** — endpoint REST + streaming SSE pour les réponses token par token
- **Ingestion automatisée** — pipeline de mise à jour périodique des sources

---

## 📊 Évaluation — RAGAS

| Métrique | Score |
|---|---|
| Faithfulness | `0.xx` |
| Context Recall | `0.xx` |
| Context Precision | `0.xx` |
| Answer Relevancy | `0.xx` |

> ⚠️ Évaluation en cours — scores à venir avec le benchmark complet sur 50 Q&A annotées.

---

## 🗂️ Structure du projet

```
research-agent/
├── src/
│   ├── agents/
│   │   ├── router.py          # LangGraph router — sélection de source
│   │   ├── retriever.py       # Retrieval hybride (dense + BM25)
│   │   └── grounding.py       # Vérification des hallucinations
│   ├── sources/
│   │   ├── arxiv_loader.py    # Ingestion arXiv via API
│   │   └── gouv_loader.py     # Ingestion data.gouv.fr via CKAN API
│   ├── vectorstore/
│   │   ├── indexer.py         # Chunking sémantique + embeddings
│   │   └── retriever.py       # FAISS / Chroma query
│   ├── pipeline/
│   │   ├── graph.py           # LangGraph orchestration complète
│   │   └── memory.py          # Gestion mémoire conversationnelle
│   └── api/
│       └── main.py            # FastAPI + streaming SSE
├── ingestion/
│   ├── fetch_arxiv.py         # Fetch périodique arXiv
│   └── fetch_gouv.py          # Fetch périodique data.gouv.fr
├── evaluation/
│   ├── benchmark.py           # Pipeline RAGAS
│   └── dataset/               # Q&A annotées de référence
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🚀 Installation & lancement

### Prérequis

- Python 3.11+
- Docker (optionnel)
- Clé API OpenAI ou modèle local via Ollama

### Installation locale

```bash
# Cloner le repo
git clone https://github.com/marinaKpamegan/research-agent.git
cd research-agent

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec ta clé API et tes paramètres
```

### Variables d'environnement

```env
OPENAI_API_KEY=sk-...          # ou HUGGINGFACE_API_KEY pour les modèles open source
ARXIV_CATEGORIES=cs.AI,cs.CL,cs.IR,cs.LG
ARXIV_MAX_RESULTS=500
GOUV_API_URL=https://www.data.gouv.fr/api/1
VECTOR_STORE=faiss             # faiss ou chroma
EMBEDDING_MODEL=text-embedding-3-small
```

### Lancer l'ingestion

```bash
# Ingérer les sources (première fois)
python ingestion/fetch_arxiv.py
python ingestion/fetch_gouv.py

# Lancer l'API
uvicorn src.api.main:app --reload --port 8000
```

### Avec Docker

```bash
docker-compose up --build
```

---

## 💬 Utilisation

### Via l'API REST

```python
import requests

response = requests.post("http://localhost:8000/query", json={
    "question": "Quelles sont les dernières avancées en RAG hybride ?",
    "sources": ["arxiv", "gouv"],  # ou ["arxiv"] / ["gouv"] pour cibler
    "top_k": 5
})

print(response.json())
# {
#   "answer": "...",
#   "sources": [{"title": "...", "url": "...", "date": "..."}],
#   "faithfulness_score": 0.91
# }
```

### Streaming SSE

```python
import httpx

with httpx.stream("POST", "http://localhost:8000/query/stream",
                  json={"question": "..."}) as r:
    for chunk in r.iter_text():
        print(chunk, end="", flush=True)
```

---

## 🛣️ Roadmap

- [x] Ingestion arXiv (cs.AI, cs.CL, cs.IR, cs.LG)
- [x] Ingestion data.gouv.fr via CKAN API
- [x] Pipeline RAG LangChain de base
- [x] LangGraph orchestration multi-sources
- [x] API FastAPI + streaming SSE
- [ ] Re-ranking cross-encoder
- [ ] Grounding check anti-hallucination
- [ ] Benchmark RAGAS complet
- [ ] Démo live en ligne
- [ ] Interface Streamlit
- [ ] Mise à jour automatique des sources (cron)

---

## 🧠 Choix techniques

**Pourquoi LangGraph plutôt qu'une chaîne LangChain simple ?**
Le routing entre deux sources hétérogènes (arXiv = PDF scientifiques / data.gouv.fr = métadonnées JSON) nécessite un agent avec état et décision conditionnelle — exactement ce pour quoi LangGraph est conçu.

**Pourquoi FAISS / Chroma ?**
FAISS pour la performance en local sur un corpus de 500+ documents. Chroma pour la persistance et les filtres de métadonnées (date, catégorie, source). Le choix se configure via variable d'environnement.

**Pourquoi ces deux sources ?**
La combinaison arXiv + data.gouv.fr est rare et complémentaire : arXiv couvre la veille scientifique mondiale, data.gouv.fr apporte le contexte réglementaire et les données publiques françaises — utile pour des cas d'usage IA souveraine, exactement ce que des acteurs comme Lyha adressent.

---

## 👩‍💻 Auteure

**Falonne KPAMEGAN** — Data Scientist · Data Engineer · AI Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-falonne--kpamegan-blue?style=flat-square&logo=linkedin)](https://linkedin.com/in/falonne-kpamegan)
[![Portfolio](https://img.shields.io/badge/Portfolio-falonnekpamegan.site-teal?style=flat-square)](https://falonnekpamegan.site)
[![GitHub](https://img.shields.io/badge/GitHub-marinaKpamegan-black?style=flat-square&logo=github)](https://github.com/marinaKpamegan)

---

## 📄 Licence

MIT License — voir [LICENSE](LICENSE)
