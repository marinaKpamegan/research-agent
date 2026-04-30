# 🔍 Architecture du Système

Ce document détaille l'architecture interne et le flux de données de l'agent de recherche multimodal.

## 🏗️ Vue d'Ensemble
Research agent est un système agentique conçu pour automatiser la veille scientifique et l'analyse de données publiques. Il utilise une approche par graphe d'états pour gérer des processus de recherche complexes et non-linéaires.

---

## 🧭 Orchestration : LangGraph
Le cœur du système est défini dans `app/agents/research_agent.py`. Contrairement à une chaîne séquentielle, LangGraph permet des boucles de décision et des replis (fallbacks).

### Nœuds du Graphe
1.  **Route Query** : Un LLM (GPT-4o-mini) classifie la question pour sélectionner la source experte.
2.  **Specialized Search** : Nœuds dédiés pour `ArXiv`, `PapersWithCode` et `Data.gouv.fr`.
3.  **Search Web** : Utilise SearXNG pour trouver des URLs, puis Crawl4AI pour extraire le texte brut.
4.  **Generate Answer** : Synthèse finale à partir de tous les contextes accumulés.

### Logique de Fallback
Le graphe contient des arêtes conditionnelles (`ConditionalEdges`) qui détectent si une source spécialisée a échoué (0 résultat). Dans ce cas, le flux est redirigé vers le nœud **Search Web** pour garantir une réponse riche.

---

## 📡 Flux de Streaming (SSE)
L'interface utilisateur communique avec le backend via des **Server-Sent Events**. 
Le backend émet des événements à chaque étape cruciale :
- `thinking_block` : Contient le raisonnement brut des modèles.
- `source_selected` : Notifie l'UI de la source choisie.
- `fallback` : Indique qu'un changement de stratégie est nécessaire.
- `stream` : Tokens de la réponse finale en temps réel.

---

## 📄 Analyse Multimodale (Background Processing)
Pour éviter de bloquer la connexion SSE pendant l'analyse lourde de PDFs (qui peut prendre 30s-1min) :
1.  L'agent identifie un PDF et le met en file d'attente interne via `asyncio.create_task`.
2.  Le flux SSE se termine normalement avec une réponse initiale.
3.  Le service `PdfRagService` traite le document via un modèle de Vision (Gemini 1.5 Pro).
4.  Une fois terminé, le résumé enrichi est mis à jour dans la base de données (Historique).

---

## 📊 Pipeline d'Évaluation
Chaque interaction est passée au service `EvaluationService` qui utilise le framework **Ragas** :
- **Faithfulness** : Vérifie si la réponse est bien étayée par les sources.
- **Answer Relevance** : Mesure la pertinence de la réponse par rapport à la question.
Les scores sont stockés avec chaque entrée de l'historique pour monitorer la performance globale de l'agent.

---

## 🛠️ Services Tiers
- **OpenRouter** : Proxy vers les meilleurs modèles LLM du marché.
- **SearXNG** : Métamoteur de recherche auto-hébergé respectueux de la vie privée.
- **Crawl4AI** : Crawler optimisé pour le rendu Markdown prêt pour les LLMs.
- **Data.gouv MCP** : Serveur Model Context Protocol pour un accès structuré aux données d'État.