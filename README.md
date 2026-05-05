# 🚀 AI Research Agent: Multi-Expert Grounding System

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://python.langchain.com/docs/langgraph)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-green.svg)](https://fastapi.tiangolo.com/)

## 💼 Le Problème Business : La quête de la vérité à l'ère de l'infobésité
**"Dans un monde saturé d'informations, la rapidité d'accès à une donnée vérifiable est un avantage stratégique."**

Les experts (chercheurs, data scientists, décideurs publics) font face à un défi triple que les LLM généralistes ne peuvent résoudre seuls :

1.  **Fragmentation des Données** : L'information technique est dispersée. Un papier académique est sur **ArXiv**, alors que son implémentation et ses benchmarks sont sur **PapersWithCode**. Croiser ces deux sources manuellement est fastidieux.
2.  **Le Paradoxe de la Confiance (Hallucinations)** : Les LLM "standard" ont tendance à inventer des faits pour paraître cohérents. Pour des décisions à fort enjeu (investissements technologiques, recherche scientifique), l'incertitude est inacceptable.
3.  **Accès aux Données Publiques** : Les LLM n'ont pas d'accès direct et structuré aux datasets officiels (ex: Data.gouv.fr), rendant les recherches administratives ou budgétaires imprécises.

### 💡 La Solution : Research Agent
**Research Agent** transforme ce processus en un flux automatisé et intelligent :
- **Parallélisation Scientifique** : Pour les requêtes de recherche, il interroge simultanément **ArXiv** et **PapersWithCode**, fusionnant théorie et code en un seul flux asynchrone.
- **Ancrage (Grounding) sur Données Réelles** : Chaque affirmation est liée à une source réelle récupérée via des API spécialisées ou le protocole MCP.
- **Gain de Productivité** : Ce qui prenait 30 minutes de navigation entre différents onglets est réduit à une synthèse structurée en quelques secondes.

---

## 🏗️ Ingénierie Backend & Architecture

Le cœur du système repose sur un graphe d'états complexe développé avec **LangGraph**, conçu pour la performance et la précision.

### ⚡ Parallélisme Scientifique (Fan-out/Fan-in)
Pour les requêtes identifiées comme "Science" par le routeur LLM, le backend déclenche une exécution parallèle :
- **Node ArXiv** : Extraction de publications académiques via l'API ArXiv.
- **Node PapersWithCode** : Recherche d'implémentations GitHub et de benchmarks SOTA.
Cette architecture divise par deux le temps de réponse et permet une synthèse riche (Théorie + Code).

### 🏛️ Intégration Data.gouv via MCP
L'agent utilise le **Model Context Protocol (MCP)** pour interroger dynamiquement les API de l'État français. 
- **Tooling Dynamique** : Nettoyage d'arguments à la volée pour assurer la stabilité des appels API.
- **Récupération de Statistiques** : Capacité à extraire des chiffres précis (ex: budgets ministériels) directement depuis les datasets officiels.

### 🔍 RAG Hybride & Vision Asynchrone
- **Scraping Intelligent** : Utilisation de **Crawl4AI** pour transformer des pages web complexes en Markdown propre.
- **Vector Search** : Stockage local éphémère dans **FAISS** pour un RAG contextuel précis sur les contenus fraîchement crawllés.

---

## ✨ Fonctionnalités orientées "Production"

### 📡 Streaming Granulaire (SSE)
L'interface ne "load" pas dans le vide. Le backend streame en temps réel via Server-Sent Events :
- **Reasoning Panel** : Les étapes de réflexion de l'agent.
- **Status Events** : Sélection de source, démarrage des recherches parallèles

### 🛡️ Robustesse & Observabilité
- **Error Handling Front-to-Back** : Interception des erreurs de session (401) et des crashs backend avec notification immédiate au frontend via le flux SSE.
- **Recursion Guard** : Limite de profondeur du graphe pour éviter les boucles infinies sur des recherches complexes.
- **Évaluation RAGAS** : Pipeline intégré pour mesurer la fidélité de la réponse par rapport au contexte extrait.

---

## 🛠️ Stack Technique

- **Framework** : FastAPI (Python 3.12)
- **Intelligence** : LangGraph, LangChain, OpenRouter (Gemini 2.0 Flash, GPT-4o-mini)
- **Data & Search** : SearXNG (Web), MCP (Data.gouv), ArXiv, PapersWithCode
- **Parsing & Vector** : Crawl4AI, FAISS, SQLAlchemy (PostgreSQL)
- **Monitoring** : Ragas (Évaluation de la qualité)

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
