# research-agent

🕵️‍♂️ Research Agent AI (WIP)
Un agent de recherche autonome de nouvelle génération capable d'explorer le web, de structurer des connaissances et de synthétiser des rapports sourcés.

Ce projet est un assistant de recherche intelligent conçu pour transformer des requêtes complexes en rapports structurés. Contrairement à un chatbot classique, cet agent planifie, navigue, extrait et auto-corrige ses recherches de manière autonome.

🚀 Vision du Projet
L'objectif est de résoudre le problème des hallucinations et de la péremption des données des LLMs classiques en fournissant un système de RAG Agentique (Retrieval-Augmented Generation) qui s'appuie sur des faits réels et vérifiables en temps réel.

🧠 Fonctionnalités Clés
- Orchestration avec LangGraph : Gestion des cycles de réflexion (Reasoning loops) et persistance de l'état (State).

- Smart Scraping avec Crawl4AI : Extraction de contenu web asynchrone converti en Markdown pour optimiser les tokens.

- Multi-Source Retrieval : Intégration flexible (SearXNG) pour une exploration exhaustive.

- Reranking de Précision : Utilisation du modèle ms-marco-MiniLM-L-6-v2 pour filtrer les sources par pertinence sémantique réelle.

- Mémoire Vectorielle Locale : Indexation rapide via FAISS avec des embeddings multilingues (BGE-M3).

- Analyse Multimodale : (Prévu) Capacité à interpréter des graphiques via SigLIP.

Run the API:

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Run the quick test script:

```bash
python scripts/test_agent.py

Open the API docs at: http://127.0.0.1:8000/api/docs
```
# research-agent
