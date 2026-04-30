# 🧠 Research Agent (Backend)

Bienvenue dans le cœur moteur de **Research Agent**, un service de recherche agentique haute performance construit avec **FastAPI** et **LangGraph**. Ce backend orchestre l'exploration de sources multiples, l'analyse visuelle de documents et la synthèse de réponses sourcées.

---

## 🏗️ Architecture & Flux de Données

Le backend repose sur un graphe d'états (StateGraph) qui gère intelligemment le flux de recherche :

1.  **Router (LLM)** : Analyse la question et choisit la source la plus pertinente (ArXiv, PWC, Data.gouv ou Web).
2.  **Search Nodes** : Interrogent les APIs spécialisées ou le moteur de recherche **SearXNG**.
3.  **Extraction (Crawl4AI)** : Scrape et nettoie le contenu des pages web pour un contexte de haute qualité.
4.  **Fallback Logic** : Si une source experte échoue, l'agent bascule automatiquement vers une recherche web généraliste.
5.  **Synthèse (OpenRouter)** : Génère une réponse finale en citant précisément les sources utilisées.

---

## ✨ Fonctionnalités Avancées

### 🚀 Traitement Asynchrone & Non-Bloquant
L'utilisation de `asyncio.create_task` permet de détacher les tâches lourdes du cycle de réponse HTTP :
- **Analyse PDF Vision** : Les documents volumineux sont traités en arrière-plan via des modèles de vision.
- **Évaluation automatique** : Chaque réponse est évaluée par le pipeline **Ragas** (Fidélité, Pertinence) sans faire attendre l'utilisateur.

### 📡 Streaming Granulaire (SSE)
Le backend expose un endpoint `/api/query/stream` qui renvoie :
- Les blocs de réflexion de l'agent (**Thought Blocks**).
- Le flux de tokens de la réponse finale.
- Les événements de sélection de source et de fallback.

### 📊 Intégration Data.gouv (MCP)
Utilisation du protocole **Model Context Protocol (MCP)** pour interroger de manière "stateless" les jeux de données publics français, permettant une extraction de chiffres et de statistiques officielles.

---

## 🛠️ Stack Technique

- **Framework API** : [FastAPI](https://fastapi.tiangolo.com/)
- **Orchestration d'Agents** : [LangGraph](https://python.langchain.com/docs/langgraph)
- **LLM Gateway** : [OpenRouter](https://openrouter.ai/) (Gemini 1.5 Pro, GPT-4o-mini)
- **Extraction Web** : [Crawl4AI](https://crawl4ai.com/)
- **Recherche Web** : [SearXNG](https://docs.searxng.org/)
- **Base de Données** : PostgreSQL avec [SQLAlchemy](https://www.sqlalchemy.org/)
- **Évaluation** : [Ragas](https://docs.ragas.io/)
- **Vector Store** : FAISS (pour le RAG local sur le contenu crawlé)

---

## ⚙️ Installation & Lancement Local

### 1. Prérequis
- Python 3.12+
- PostgreSQL
- Instance SearXNG (ou accès à une instance distante)

### 2. Installation
```bash
git clone <votre-repo-backend>
cd research-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration (Variables d'environnement)
Créez un fichier `.env` à la racine :
```env
# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/researchagent

# LLM APIs
OPENROUTER_API_KEY=votre_cle_openrouter
OPENAI_API_KEY=votre_cle_openai (pour les embeddings)

# Services
SEARXNG_URL=http://votre-instance-searxng:8080
MCP_SERVER=https://mcp.data.gouv.fr/mcp

# Auth
SECRET_KEY=votre_cle_secrete_jwt
```

### 4. Initialisation de la Base de Données
```bash
# Assurez-vous que PostgreSQL est lancé et que la DB existe
python fix_db.py # Script utilitaire pour s'assurer que les tables sont correctes
```

### 5. Lancement du serveur
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📂 Structure du Code

- `app/api` : Endpoints FastAPI (auth, query, preferences).
- `app/agents` : Cœur de la logique agentique et définition du graphe LangGraph.
- `app/services` : Services tiers (ArXiv, PWC, PDF Visual, SearXNG, Crawl4AI).
- `app/db` : Modèles SQLAlchemy et repositories.
- `app/schemas` : Modèles Pydantic pour la validation API.

---

## 📄 Licence
[MIT](LICENSE)
