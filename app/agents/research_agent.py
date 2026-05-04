import asyncio
import logging
from typing import List, Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

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
        workflow.add_node("search_web", self._search_web)
        workflow.add_node("generate_answer", self._generate_answer)
        
        # Define edges
        workflow.add_edge(START, "route_query")
        
        # Conditional edge: route to science (parallel), datagouv or web
        workflow.add_conditional_edges(
            "route_query",
            self._route_logic, 
            {
                "search_arxiv": "search_arxiv",
                "search_pwc": "search_pwc",
                "search_datagouv": "search_datagouv",
                "search_web": "search_web"
            }
        )
        
        # All search nodes point to answer generation
        workflow.add_edge("search_arxiv", "generate_answer")
        workflow.add_edge("search_pwc", "generate_answer")
        workflow.add_edge("search_datagouv", "generate_answer")
        workflow.add_edge("search_web", "generate_answer")
        
        workflow.add_edge("search_web", "generate_answer")
        workflow.add_edge("generate_answer", END)
        
        return workflow.compile()

    # --- Nodes ---

    async def _route_query(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
        """Node: Use LLM to analyze the question and select the source."""
        question = state["question"]
        logger.info(f"Routing query: {question}")
        
        prompt = f"""Tu es un routeur d'intentions expert. Analyse la question de l'utilisateur et détermine la meilleure source.

## RÈGLES CRITIQUES :
1. Si la question mentionne un **Ministère**, une **Administration**, une **Collectivité** ou l'**État Français** (ex: Culture, Santé, Rhône, INSEE, Gouvernement) -> UTILISE TOUJOURS `datagouv`.
2. Si la question porte sur des **Papiers de recherche**, de l'**IA théorique**, ou des **Benchmarks de modèles** -> UTILISE `science`.
3. Pour tout le reste (entreprises, tutoriels, actu générale) -> UTILISE `web`.

## Catégories :
- science : Recherche scientifique, IA, Physique, Maths, Benchmarks, Code.
- datagouv : Données publiques françaises, Ministères, Budgets, Statistiques d'état (INSEE), Décrets, Territoires.
- web : Actualité, Entreprises (ESN, startups), Culture générale.

## Exemples
| Question | Source | Raison |
|---|---|---|
| "Datasets du ministère de la culture" | données gouvernementales | data gouvernementale | datagouv | Ministère français |
| "Budget de l'éducation nationale" | datagouv | Administration française |
| "Papiers sur le RAG" | science | Recherche IA |
| "Liste des ESN à Lyon" | web | Entreprises |

## Réponse
Réponds UNIQUEMENT par un seul mot parmi : science, datagouv, web
Aucune ponctuation, aucune explication.
"""
        from langchain_openai import ChatOpenAI
        from app.core.config import settings
        
        llm = ChatOpenAI(
            base_url=settings.OPENROUTER_API_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.DEFAULT_AI_MODEL,
            temperature=0,
            max_tokens=100,
            streaming=True
        ).with_config({"run_name": "route_query"})
        
        messages = [{"role": "user", "content": prompt}]
        res = await llm.ainvoke(messages, config=config)
        source = res.content.strip().lower()
        
        # Nettoyage
        if "science" in source or "arxiv" in source or "papers" in source:
            selected = "science"
        elif "datagouv" in source:
            selected = "datagouv"
        else:
            selected = "web"
            
        logger.info(f"Selected source: {selected}")
        return {"selected_source": selected}

    def _route_logic(self, state: AgentState) -> List[str]:
        """Logic for parallel routing."""
        source = state.get("selected_source", "web")
        if source == "science":
            return ["search_arxiv", "search_pwc"]
        return [f"search_{source}"]

    async def _search_arxiv(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
        """Node: Search ArXiv for scientific papers."""
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

    async def _search_pwc(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
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

    async def _search_datagouv(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
        """Node: Search Data.gouv.fr using MCP."""
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
                        model=settings.DEFAULT_AI_MODEL,
                        temperature=0.8,
                        max_tokens=5000,
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
                        f"   - IMPORTANT : Pour 'query_resource_data', ne passe JAMAIS de valeur 'null' ou 'None' aux arguments optionnels (filter_operator, etc.). Omet-les simplement ou passe une chaîne vide si l'outil l'exige.\n"
                        f"   - Si c'est un format non-indexé, utilise 'download_and_parse_resource'.\n"
                        f"   - Si c'est un gros PDF (rapport gouvernemental), tu DOIS appeler notre outil asynchrone 'query_pdf_document' avec l'URL.\n"
                        f"Étape 4 - FINALISATION : Ne retourne JAMAIS de simples métadonnées. Je veux la VRAIE réponse factuelle (les chiffres, l'info).\n"
                        f"TRÈS IMPORTANT : Si un outil ('query_pdf_document' ou autre) te répond que le document a été mis en 'file d'attente' ou 'tâche de fond', C'EST UN SUCCÈS COMPLET de l'étape 3. N'essaie PAS de relancer un outil. Arrête-toi IMMÉDIATEMENT et donne ta réponse finale en notifiant l'utilisateur !"
                    )
                    # 5. Exécution de l'agent
                    final_msg = ""
                    discovered_resources = {} # ID -> {title, url}
                    used_resource_ids = set()
                    
                    try:
                        from langgraph.errors import GraphRecursionError
                    except ImportError:
                        GraphRecursionError = Exception

                    try:
                        async for agent_event in agent.astream_events(
                            {"messages": [{"role": "user", "content": prompt}]},
                            config={"recursion_limit": 15}, # max recursive call limit
                            version="v2"
                        ):
                            if agent_event["event"] == "on_tool_start":
                                tool_name = agent_event["name"]
                                tool_input = agent_event["data"].get("input", {})
                                logger.info(f"[Data.Gouv Inner Agent] Call Tool: {tool_name} with args: {tool_input}")
                                
                                # Track which resource is being used
                                if isinstance(tool_input, dict) and "resource_id" in tool_input:
                                    used_resource_ids.add(tool_input["resource_id"])
                                    
                            elif agent_event["event"] == "on_tool_end":
                                tool_name = agent_event["name"]
                                tool_output = agent_event["data"].get("output", "")
                                logger.info(f"[Data.Gouv Inner Agent] Return Tool: {str(tool_output)[:200]}...")
                                
                                # Parse output to find resource metadata (Title, ID, URL)
                                if tool_name in ["list_dataset_resources", "get_resource_info", "search_datasets"]:
                                    import re
                                    # Regex simplifiée pour capturer les blocs de ressources
                                    # Le format MCP Stateless est souvent textuel
                                    res_matches = re.finditer(r"Resource ID: ([a-f0-9\-]+).*?URL: (https?://[^\s\n]+)", str(tool_output), re.DOTALL | re.IGNORECASE)
                                    for m in res_matches:
                                        r_id, r_url = m.groups()
                                        if r_id not in discovered_resources:
                                            # On essaie de remonter un peu pour le titre
                                            title_match = re.search(r"(\d+\.\s+)?([^\n]+)\n\s+Resource ID: " + re.escape(r_id), str(tool_output))
                                            r_title = title_match.group(2).strip() if title_match else f"Fichier Data.gouv ({r_id[:8]})"
                                            discovered_resources[r_id] = {"title": r_title, "url": r_url}
                                           

                            elif agent_event["event"] == "on_chat_model_stream":
                                chunk = agent_event["data"]["chunk"].content
                                if chunk:
                                    final_msg += chunk
                            elif agent_event["event"] == "on_chain_end" and agent_event["name"] == "agent":
                                output = agent_event["data"].get("output", {})
                                msgs = output.get("messages", [])
                                if msgs:
                                    final_msg = msgs[-1].content

                        logger.info(f"Discovered resources: {discovered_resources}")         
                    
                    except GraphRecursionError as e:
                        logger.warning(f"L'Agent MCP a bouclé et atteint sa limite de récursion. Arrêt forcé. Message partiel: {final_msg}")
                        if not final_msg:
                            final_msg = "L'exploration des données a été interrompue en raison d'une boucle technique."

                    logger.info(f"Data.gouv response: {final_msg}")

                    # Ajout des ressources réellement utilisées comme sources distinctes
                    sources_added = 0
                    for r_id in used_resource_ids:
                        if r_id in discovered_resources:
                            res = discovered_resources[r_id]
                            content.append({
                                "url": res["url"],
                                "title": f"[Data.Gouv] {res['title']}",
                                "content": f"Données extraites de ce fichier pour répondre à : {question}",
                                "score": 1.1 # Priorité légèrement supérieure car c'est de la donnée brute
                            })
                            sources_added += 1
                    
                    # On ajoute quand même l'analyse globale si elle contient du texte
                    if final_msg:
                        content.append({
                            "url": url,
                            "title": "[Data.Gouv] Synthèse de l'Analyse MCP",
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

    async def _search_web(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
        """Node: Search Web with SearXNG and crawl."""
        question = state["question"]
        logger.info(f"Searching Web (SearXNG) for: {question}")
        
        from langchain_community.utilities import SearxSearchWrapper
        from app.core.config import settings
        from app.services.crawling_service import CrawlingService
        
        query_prompt = f"Génère une requête très courte (max 5 mots clés) pour chercher sur le web à partir de cette question: {question}\nRéponds UNIQUEMENT avec les mots clés sans ponctuation."
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            base_url=settings.OPENROUTER_API_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.DEFAULT_AI_MODEL,
            temperature=0,
            max_tokens=100,
            streaming=True
        ).with_config({"run_name": "generate_web_query"})
        
        messages = [{"role": "user", "content": query_prompt}]
        res = await llm.ainvoke(messages, config=config)
        web_query = res.content.strip()
        
        logger.info(f"Web query: {web_query}")
        
        try:
            searx = SearxSearchWrapper(searx_host=settings.SEARXNG_URL)
            # On utilise results() pour obtenir des dictionnaires avec 'link' et 'title'
            results = await asyncio.to_thread(searx.results, web_query, num_results=15)
            urls = [r["link"] for r in results if "link" in r]
            logger.info(f"Web results: {urls}")
        except Exception as e:
            logger.error(f"SearXNG error: {e}")
            urls = []
            
        new_content = []
        if urls:
            crawler = CrawlingService()
            scraped = await crawler.scrape_urls(urls)
            for item in scraped:
                new_content.append({
                    "url": item["url"], 
                    "title": item["title"] or "Web Page", 
                    "content": item["markdown"],
                    "score": 1.0
                })
                
        return {"crawled_content": new_content, "urls": urls}

    async def _generate_answer(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
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
Réponds à la question suivante en utilisant le contexte fourni.
{interests_str}
Question: {question}

Contexte (Source interrogée : {source}):
{context_str}

Consignes :
1. Réponds de manière concise et factuelle.
2. Utilise des citations sous la forme [Source n] pour chaque information importante.
3. Si le contexte ne contient pas la réponse exacte ou exhaustive, présente les informations les plus pertinentes et les chiffres disponibles comme "éléments de réponse", plutôt que de dire que tu n'as pas d'information.
4. Réponds en français.
"""
        if source == "datagouv":
            prompt += "\nIMPORTANT : Pour Data.gouv, le contexte provient d'une exploration directe de bases de données par un expert. Tu DOIS restituer les chiffres et détails extraits, même s'ils ne couvrent qu'une partie de la question."
        from langchain_openai import ChatOpenAI
        from app.core.config import settings
        
        llm = ChatOpenAI(
            base_url=settings.OPENROUTER_API_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.DEFAULT_AI_MODEL,
            streaming=True,
            temperature=0.8,
            max_tokens=3000
        ).with_config({"run_name": "generate_answer"})
        
        messages = [{"role": "user", "content": prompt}]
        
        answer = ""
        async for chunk in llm.astream(messages, config=config):
            answer += chunk.content
        
        logger.info(f"Answer: {answer}")
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
            if kind == "on_chain_end" and langgraph_node in ["route_query", "search_arxiv", "search_pwc", "search_web"]:
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
                        "datagouv": "Source choisie : data.gouv.fr",
                        "web": "Source choisie : Web (Général)"
                    }
                    yield json.dumps({
                        "step": "source_selected",
                        "message": source_labels.get(current_source, current_source),
                        "data": {"source": current_source}
                    })
            
            # Nodes
            if kind == "on_chain_start":
                if langgraph_node == "route_query":
                    try:
                        async for event in self.graph.astream_events(initial_state, version="v2"):
                            kind = event["event"]
                            name = event["name"]
                            metadata = event.get("metadata", {})
                            langgraph_node = metadata.get("langgraph_node", "")
                            tags = event.get("tags", [])
                            
                            # Afficher le bloc de raisonnement complet à la fin du nœud
                            if kind == "on_chain_end" and langgraph_node in ["route_query", "search_arxiv", "search_pwc", "search_web"]:
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
                                        "datagouv": "Source choisie : data.gouv.fr",
                                        "web": "Source choisie : Web (Général)"
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
                                elif langgraph_node == "search_web":
                                    if current_source not in ["web", ""]:
                                        fallback_from = current_source.capitalize()
                                        if current_source == "paperswithcode": fallback_from = "PWC"
                                        if current_source == "datagouv": fallback_from = "Data.gouv"
                                        yield json.dumps({"step": "fallback", "message": f"{fallback_from} sans résultat — repli d'urgence ultime sur le Web...", "data": None})
                                    else:
                                        yield json.dumps({"step": "search_web", "message": "Recherche générale sur le Web avec SearXNG...", "data": None})
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
                                    if langgraph_node == "generate_answer" or name == "generate_answer":
                                        yield json.dumps({"step": "stream", "message": chunk, "data": None})
                                    elif langgraph_node in ["route_query", "search_arxiv", "search_pwc", "search_web"] or name in ["route_query", "generate_web_query"]:
                                        node_key = langgraph_node or name
                                        thought_buffer[node_key] = thought_buffer.get(node_key, "") + chunk
                                    
                            # Capture state updates from all nodes and the root graph
                            if kind == "on_chain_end":
                                output = event.get("data", {}).get("output", {})
                                if isinstance(output, dict):
                                    for k, v in output.items():
                                        if k in ["crawled_content", "urls", "pending_backgroundtasks"] and k in last_state and isinstance(v, list):
                                            # Accumulate lists for keys that use operator.add in AgentState
                                            for item in v:
                                                if item not in last_state[k]:
                                                    last_state[k].append(item)
                                            logger.info(f"Accumulated {k}: {len(last_state[k])} items total (added {len(v)})")
                                        else:
                                            last_state[k] = v
                                    if "answer" in output:
                                        logger.info(f"Answer updated in state (length: {len(output['answer'])})")
                                        
                    except Exception as e:
                        logger.error(f"Erreur fatale dans stream_question: {e}", exc_info=True)
                        yield json.dumps({"step": "error", "message": f"Une erreur est survenue : {str(e)}", "data": None})
                        return
                
        # Final Event
        crawled = last_state.get('crawled_content', [])
        payload = {
            "answer": last_state.get("answer", ""),
            "sources": [{"title": c.get("title", f"Source {i+1}"), "url": c["url"]} for i, c in enumerate(crawled[:20])],
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
