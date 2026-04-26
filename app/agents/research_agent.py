import logging
from typing import List, Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from app.services.openrouter_service import OpenRouterService
from app.memory.simple_memory import SimpleMemory
from app.models.research import AgentState
from app.services.pwc_service import PwcService

logger = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self, faiss_service=None, reranker=None, arxiv_service=None, mcp_service=None):
        self.memory = SimpleMemory()
        self.openrouter = OpenRouterService()
        self.faiss_service = faiss_service
        self.reranker = reranker
        self.arxiv_service = arxiv_service
        self.mcp_service = mcp_service
        self.pwc_service = PwcService()
        self.graph = self._create_research_graph()

    def _create_research_graph(self):
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("route_query", self._route_query)
        workflow.add_node("search_arxiv", self._search_arxiv)
        workflow.add_node("search_pwc", self._search_pwc)
        workflow.add_node("search_datagouv", self._search_datagouv)
        workflow.add_node("generate_answer", self._generate_answer)
        
        # Define edges
        workflow.add_edge(START, "route_query")
        
        # Conditional edge: route to arxiv, pwc or datagouv
        workflow.add_conditional_edges(
            "route_query",
            lambda state: state["selected_source"],
            {
                "arxiv": "search_arxiv",
                "paperswithcode": "search_pwc",
                "datagouv": "search_datagouv"
            }
        )
        
        # Fallback conditions
        def check_arxiv_fallback(state: AgentState) -> str:
            if not state.get("crawled_content") and state.get("selected_source") == "arxiv":
                return "search_pwc"
            return "generate_answer"
            
        def check_pwc_fallback(state: AgentState) -> str:
            if not state.get("crawled_content") and state.get("selected_source") == "paperswithcode":
                return "search_arxiv"
            return "generate_answer"
        
        workflow.add_conditional_edges("search_arxiv", check_arxiv_fallback)
        workflow.add_conditional_edges("search_pwc", check_pwc_fallback)
        workflow.add_edge("search_datagouv", "generate_answer")
        workflow.add_edge("generate_answer", END)
        
        return workflow.compile()

    # --- Nodes ---

    async def _route_query(self, state: AgentState) -> Dict[str, Any]:
        """Node: Use LLM to analyze the question and select the source."""
        question = state["question"]
        logger.info(f"Routing query: {question}")
        
        prompt = f"""Tu es un routeur de recherche. Ta seule tâche est de choisir la bonne source pour répondre à cette question.

Question : "{question}"

## Règle fondamentale
Analyse l'INTENTION de la question, pas ses mots-clés superficiels.
"entreprises de data à Lyon" → l'intention est de TROUVER DES ENTREPRISES en France → datagouv
"comment fonctionne un modèle de data augmentation" → l'intention est de COMPRENDRE UN CONCEPT → arxiv

## Sources disponibles

"datagouv" — Données publiques françaises
→ Choisis cette source si la question cherche des ACTEURS, des LIEUX ou des CHIFFRES en France :
  - Entreprises, sociétés, startups, ESN, agences localisées en France (même si elles font de l'IA ou de la data)
  - Statistiques économiques, sociales, démographiques françaises
  - Budget, administrations, collectivités, marchés publics
  - Transport, énergie, écologie, immobilier, santé en France
  - Élections, recensements, emploi par région ou département
⚠️ Si la question mentionne une ville française, une entreprise ou un secteur économique en France → datagouv en priorité absolue, même si les mots "IA" ou "data" apparaissent.

"arxiv" — Recherche académique et scientifique
→ Choisis cette source si la question cherche à COMPRENDRE ou EXPLORER un concept scientifique :
  - Fonctionnement théorique d'un algorithme ou d'une architecture (transformers, diffusion, RL…)
  - Publications, auteurs, papiers de recherche
  - Mathématiques, physique, sciences fondamentales
  - État de l'art théorique sur un sujet
⚠️ Ne jamais choisir arxiv si la question mentionne une ville, une entreprise ou un territoire français.

"paperswithcode" — Implémentations et benchmarks
→ Choisis cette source si la question cherche du CODE ou des PERFORMANCES :
  - Implémentations GitHub, librairies, frameworks
  - Benchmarks, scores, leaderboards, métriques de performance
  - Modèles pré-entraînés, datasets de test
  - "Comment implémenter X", "quel modèle est le meilleur pour Y"
⚠️ Ne jamais choisir paperswithcode si la question porte sur des acteurs économiques réels.

## Exemples de décision

| Question | Source | Raison |
|---|---|---|
| "entreprises IA à Lyon" | datagouv | recherche d'acteurs économiques localisés |
| "startups data en Île-de-France" | datagouv | entreprises en France |
| "nombre d'emplois dans le numérique en France" | datagouv | statistique économique française |
| "budget IA du gouvernement français 2024" | datagouv | données publiques françaises |
| "comment fonctionne l'attention dans les transformers" | arxiv | concept théorique académique |
| "derniers papiers sur le RAG hybride" | arxiv | recherche de publications |
| "état de l'art sur la détection d'anomalies" | arxiv | survey académique |
| "meilleures implémentations de RAG sur GitHub" | paperswithcode | recherche de code |
| "quel LLM a le meilleur score sur MMLU" | paperswithcode | benchmark de performance |
| "fine-tuner BERT en Python" | paperswithcode | implémentation technique |

## Réponse
Réponds UNIQUEMENT par un seul mot parmi : arxiv, paperswithcode, datagouv
Aucune ponctuation, aucune explication.
"""
        messages = [{"role": "user", "content": prompt}]
        response = await self.openrouter.create_chat_completion(messages)
        source = self.openrouter.extract_response_content(response).strip().lower()
        
        # Fallback sanitize
        if "datagouv" in source:
            selected = "datagouv"
        elif "papers" in source or "code" in source or "pwc" in source:
            selected = "paperswithcode"
        else:
            selected = "arxiv"
            
        logger.info(f"Selected source: {selected}")
        return {"selected_source": selected}

    async def _search_arxiv(self, state: AgentState) -> Dict[str, Any]:
        """Node: Search Arxiv for papers."""
        question = state["question"]
        logger.info(f"Searching ArXiv for: {question}")
        
        # We can extract keywords to search better, but arxiv service accepts free text
        # To make it better, ask LLM for a concise query string
        query_prompt = f"Génère une requête courte (max 3 mots clés) en Anglais pour chercher sur arxiv à partir de cette question: {question}\nRéponds UNIQUEMENT avec les mots clés."
        messages = [{"role": "user", "content": query_prompt}]
        res = await self.openrouter.create_chat_completion(messages)
        arxiv_query = self.openrouter.extract_response_content(res).strip()
        
        logger.info(f"ArXiv query translation: {arxiv_query}")
        
        papers = []
        if self.arxiv_service:
            papers = self.arxiv_service.search_papers(arxiv_query, max_results=3)
            
        content = []
        for p in papers:
            content.append({
                "url": p["pdf_url"] or p["id"],
                "title": f"[ArXiv] {p['title']}",
                "content": f"Authors: {', '.join(p['authors'])}\nSummary: {p['summary']}",
                "score": 1.0
            })
            
        return {"crawled_content": content}

    async def _search_pwc(self, state: AgentState) -> Dict[str, Any]:
        """Node: Search Papers With Code."""
        question = state["question"]
        logger.info(f"Searching Papers With Code for: {question}")
        
        query_prompt = f"Génère une requête courte (max 3 mots clés) en Anglais pour chercher sur paperswithcode API à partir de cette question: {question}\nRéponds UNIQUEMENT avec les mots clés."
        messages = [{"role": "user", "content": query_prompt}]
        res = await self.openrouter.create_chat_completion(messages)
        pwc_query = self.openrouter.extract_response_content(res).strip()
        
        logger.info(f"PWC query translation: {pwc_query}")
        
        content = await self.pwc_service.search_papers(pwc_query, max_results=3)
        return {"crawled_content": content}

    async def _search_datagouv(self, state: AgentState) -> Dict[str, Any]:
        """Node: Search Datagouv via MCP with SSE and create_react_agent."""
        question = state["question"]
        logger.info(f"Searching Data.gouv.fr (MCP) for: {question}")
        
        from app.core.config import settings
        from langgraph.prebuilt import create_react_agent
        from langchain_openai import ChatOpenAI
        from langchain_core.tools import StructuredTool
        from app.services.pdf_rag_service import PdfRagService
        
        content = []
        url = settings.MCP_SERVER
        
        if self.mcp_service:
            try:
                # 1. Utilisation du service HTTP Stateless de Data.gouv.fr
                tools = await self.mcp_service.get_langchain_tools(url)
                
                # Ajout de l'outil autonome d'extraction PDF
                bg_tasks_list = []
                
                async def read_pdf_url(pdf_url: str, search_query: str) -> str:
                    """Délègue l'analyse d'un PDF distant à une tâche de fond systémique."""
                    bg_tasks_list.append({"type": "pdf_visual", "url": pdf_url, "query": search_query})
                    return "Le document a bien été mis en file d'attente système pour analyse. Termine ton message en rassurant l'utilisateur et en lui précisant de vérifier son Historique (History) dans 1 à 2 minutes environ."
                
                pdf_tool = StructuredTool.from_function(
                    coroutine=read_pdf_url,
                    name="query_pdf_document",
                    description="Permet de confier la lecture d'un fichier PDF distant (via son URL) à un modèle de vision surpuissant en tâche de fond."
                )
                tools.append(pdf_tool)
                
                # 2. Si Data.Gouv a bien répondu (tools > 0)
                if tools:
                    logger.info(f"Data.gouv tools: {tools}")
                    # 3. Initialiser le ChatOpenAI vers l'endpoint (OpenRouter dans ce cas)
                    llm = ChatOpenAI(
                        base_url=settings.OPENROUTER_API_URL, 
                        api_key=settings.OPENROUTER_API_KEY, 
                        model="openai/gpt-4o-mini",
                        temperature=0.8,
                        streaming=True
                    )
                    
                    # 4. Le create_react_agent gère l'orchestration des outils MCP nativement.
                    agent = create_react_agent(llm, tools, checkpointer=None)
                    
                    prompt = (
                        f"Tu es un agent Data Analyst expert de Data.gouv.fr. Règle absolue : respecte STRICTEMENT cette méthode en entonnoir pour répondre à : '{question}'.\n"
                        f"Étape 1 - DÉCOUVERTE : Cherche les datasets avec 'search_datasets'. Trouve l'ID du plus pertinent.\n"
                        f"Étape 2 - REPÉRAGE : Utilise 'list_dataset_resources' avec cet ID pour voir les fichiers. Cible un CSV, XLSX ou JSON.\n"
                        f"Étape 3 - EXTRACTION FACTUELLE :\n"
                        f"   - Si c'est un fichier de données indexé, utilise 'query_resource_data' pour en extraire des chiffres précis.\n"
                        f"   - Si c'est un format non-indexé, utilise 'download_and_parse_resource'.\n"
                        f"   - Si c'est un gros PDF (rapport gouvernemental), tu DOIS appeler notre outil asynchrone 'query_pdf_document' avec l'URL.\n"
                        f"Étape 4 - FINALISATION : Ne retourne JAMAIS de simples métadonnées. Je veux la VRAIE réponse factuelle (les chiffres, l'info).\n"
                        f"TRÈS IMPORTANT : Si un outil ('query_pdf_document' ou autre) te répond que le document a été mis en 'file d'attente' ou 'tâche de fond', C'EST UN SUCCÈS COMPLET de l'étape 3. N'essaie PAS de relancer un outil. Arrête-toi IMMÉDIATEMENT et donne ta réponse finale en notifiant l'utilisateur !"
                    )
                    # 5. Exécution de l'agent
                    final_msg = ""
                    try:
                        from langgraph.errors import GraphRecursionError
                    except ImportError:
                        GraphRecursionError = Exception

                    try:
                        async for agent_event in agent.astream_events(
                            {"messages": [{"role": "user", "content": prompt}]},
                            config={"recursion_limit": 25},
                            version="v2"
                        ):
                            if agent_event["event"] == "on_tool_start":
                                tool_name = agent_event["name"]
                                tool_input = agent_event["data"].get("input", "")
                                logger.info(f"[Data.Gouv Inner Agent] Call Tool: {tool_name} with args: {tool_input}")
                            elif agent_event["event"] == "on_tool_end":
                                tool_output = agent_event["data"].get("output", "")
                                logger.info(f"[Data.Gouv Inner Agent] Return Tool: {str(tool_output)[:200]}...")
                            elif agent_event["event"] == "on_chat_model_stream":
                                chunk = agent_event["data"]["chunk"].content
                                if chunk:
                                    final_msg += chunk
                            elif agent_event["event"] == "on_chain_end" and agent_event["name"] == "agent":
                                output = agent_event["data"].get("output", {})
                                msgs = output.get("messages", [])
                                if msgs:
                                    final_msg = msgs[-1].content
                    except GraphRecursionError as e:
                        logger.warning(f"L'Agent MCP a bouclé et atteint sa limite de récursion (max 8). Arrêt forcé. Message partiel: {final_msg}")
                        if not final_msg:
                            final_msg = "L'exploration des données a été interrompue en raison d'une boucle technique de l'API Data.gouv."

                    logger.info(f"Data.gouv response: {final_msg}")

                    content.append({
                        "url": url,
                        "title": "[Data.Gouv] Analyse de Données MCP",
                        "content": final_msg,
                        "score": 1.0
                    })
                else:
                    content.append({
                        "url": url, 
                        "title": "Erreur Data.gouv", 
                        "content": "Aucun outil MCP récupéré via la connexion Stateless HTTP."
                    })
            except Exception as e:
                logger.error(f"Erreur d'exécution de l'agent Datagouv: {e}")
                content.append({
                    "url": url, 
                    "title": "Erreur Data.gouv", 
                    "content": f"Echec de connexion MCP SSE : {e}"
                })
                
        return {"crawled_content": content, "pending_backgroundtasks": bg_tasks_list if 'bg_tasks_list' in locals() else []}

    async def _generate_answer(self, state: AgentState) -> Dict[str, Any]:
        """Node: Synthesize a final answer from all retrieved context and keywords."""
        question = state["question"]
        content = state.get("crawled_content", [])
        interests = state.get("interests", [])
        source = state.get("selected_source", "inconnue")
        
        logger.info(f"Generating final answer for: {question} from source: {source}")
        
        if not content:
            return {"answer": f"Désolé, je n'ai trouvé aucune information pertinente sur la source '{source}' pour répondre à votre question."}
            
        # Prepare context with titles and URLs for the LLM
        context_blocks = []
        for i, c in enumerate(content):
            context_blocks.append(f"Source [{i+1}]: {c.get('title', 'Sans titre')}\nURL: {c['url']}\nContenu: {c['content'][:3000]}")
            
        context_str = "\n\n---\n\n".join(context_blocks)
        interests_str = f"L'utilisateur s'intéresse particulièrement à : {', '.join(interests)}\n" if interests else ""
        
        prompt = f"""Tu es un assistant de recherche expert spécialisé en données scientifiques (ArXiv) et publiques (Data.gouv.fr).
Réponds à la question suivante en utilisant UNIQUEMENT le contexte fourni.
{interests_str}
Question: {question}

Contexte (Source interrogée : {source}):
{context_str}

Consignes :
1. Réponds de manière concise et factuelle.
2. Utilise des citations sous la forme [Source n] pour chaque information importante.
3. Si le contexte ne contient pas de données directes pour répondre précisément, résume ce que le contexte indique et précise que tu manques d'informations pour être exhaustif.
4. Réponds en français.
"""
        from langchain_openai import ChatOpenAI
        from app.core.config import settings
        
        llm = ChatOpenAI(
            base_url=settings.OPENROUTER_API_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model="openai/gpt-4o-mini",
            streaming=True,
            temperature=0.3
        ).with_config({"run_name": "generate_answer"})
        
        messages = [{"role": "user", "content": prompt}]
        
        answer = ""
        async for chunk in llm.astream(messages):
            answer += chunk.content
        
        return {"answer": answer}

    async def stream_question(self, question: str, interests: List[str] = None, preferred_links: List[str] = None):
        """Main entry point for streaming: Execute graph and yield events at fine granularity."""
        initial_state = {
            "question": question,
            "interests": interests or [],
            "preferred_links": preferred_links or [],
            "keywords": [],
            "urls": [],
            "crawled_content": [],
            "pending_backgroundtasks": [],
            "selected_source": "",
            "fallback_to": "",
            "answer": ""
        }
        
        import json
        yield json.dumps({"step": "start", "message": f"Reçu : '{question}'", "data": None})
        
        last_state = initial_state
        current_source = ""
        thought_buffer = {}
        
        async for event in self.graph.astream_events(initial_state, version="v2"):
            kind = event["event"]
            name = event["name"]
            metadata = event.get("metadata", {})
            langgraph_node = metadata.get("langgraph_node", "")
            tags = event.get("tags", [])
            
            # Afficher le bloc de raisonnement complet à la fin du nœud
            if kind == "on_chain_end" and langgraph_node in ["route_query", "search_arxiv", "search_pwc"]:
                thought = thought_buffer.get(langgraph_node, "")
                if thought:
                    yield json.dumps({"step": "thinking_block", "message": thought, "data": None})
                    thought_buffer[langgraph_node] = ""
            
            # Capturer la source choisie dès que le router termine
            if kind == "on_chain_end" and langgraph_node == "route_query":
                output = event["data"].get("output", {})
                if isinstance(output, dict) and "selected_source" in output:
                    current_source = output["selected_source"]
                    source_labels = {
                        "arxiv": "Source choisie : arXiv",
                        "paperswithcode": "Source choisie : Papers With Code",
                        "datagouv": "Source choisie : data.gouv.fr"
                    }
                    yield json.dumps({
                        "step": "source_selected",
                        "message": source_labels.get(current_source, current_source),
                        "data": {"source": current_source}
                    })
            
            # Nodes
            if kind == "on_chain_start":
                if langgraph_node == "route_query":
                    yield json.dumps({"step": "route_query", "message": "Analyse de la demande... Catégorie en cours de sélection.", "data": None})
                elif langgraph_node == "search_arxiv":
                    if current_source == "paperswithcode":
                        yield json.dumps({"step": "fallback", "message": "Papers With Code sans résultat — repli d'urgence sur ArXiv...", "data": None})
                    else:
                        yield json.dumps({"step": "search_arxiv", "message": "Recherche sur ArXiv des articles scientifiques fondamentaux...", "data": None})
                elif langgraph_node == "search_pwc":
                    if current_source == "arxiv":
                        yield json.dumps({"step": "fallback", "message": "ArXiv sans résultat — repli d'urgence sur Papers With Code...", "data": None})
                    else:
                        yield json.dumps({"step": "search_pwc", "message": "Recherche sur Papers With Code (GitHub & benchmarks)...", "data": None})
                elif langgraph_node == "search_datagouv":
                    yield json.dumps({"step": "search_datagouv", "message": "Consultation du catalogue d'État Data.gouv.fr...", "data": None})
                elif langgraph_node == "generate_answer":
                    yield json.dumps({"step": "generate_answer", "message": "Génération de la réponse finale...", "data": None})
                    
            # Reasoning: Tools
            if kind == "on_tool_start":
                if name == "query_pdf_document":
                    yield json.dumps({"step": "reasoning", "message": "En cours d'analyse du document PDF via vision (Gemini)...", "data": None})
                else:
                    yield json.dumps({"step": "reasoning", "message": f"Utilisation de l'outil : {name}", "data": None})
                    
            # Tokens
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk and isinstance(chunk, str):
                    if langgraph_node == "generate_answer":
                        yield json.dumps({"step": "stream", "message": chunk, "data": None})
                    elif langgraph_node in ["route_query", "search_arxiv", "search_pwc"]:
                        thought_buffer[langgraph_node] = thought_buffer.get(langgraph_node, "") + chunk
                    
            # Capture final state
            if kind == "on_chain_end" and name == "LangGraph":
                output = event["data"].get("output", {})
                if output:
                    last_state.update(output)
                
        # Final Event
        crawled = last_state.get('crawled_content', [])
        payload = {
            "answer": last_state.get("answer", ""),
            "sources": [{"title": c.get("title", f"Source {i+1}"), "url": c["url"]} for i, c in enumerate(crawled[:5])],
            "selected_source": last_state.get("selected_source", ""),
            "pending_backgroundtasks": last_state.get("pending_backgroundtasks", []),
            "_raw_crawled": crawled
        }
        yield json.dumps({"step": "complete", "message": "Terminé.", "data": payload})

    async def handle_question(self, question: str, interests: List[str] = None, preferred_links: List[str] = None) -> Dict[str, Any]:
        """Main entry point: Run the LangGraph workflow and return a structured result."""
        initial_state = {
            "question": question,
            "interests": interests or [],
            "preferred_links": preferred_links or [],
            "keywords": [],
            "urls": [],
            "crawled_content": [],
            "pending_backgroundtasks": [],
            "selected_source": "",
            "fallback_to": "",
            "answer": ""
        }
        
        # Execute the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        # Create a structured result
        from app.models.research import ResearchResult
        result = ResearchResult(
            question=question,
            interests=final_state["interests"],
            preferred_links=final_state["preferred_links"],
            keywords=final_state["keywords"],
            urls=final_state["urls"],
            content=final_state["crawled_content"],
            answer=final_state.get("answer", "")
        )
        
        # Store in memory
        self.memory.add(result.dict())
        
        return result.dict()
