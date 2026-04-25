import logging
from typing import List, Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from app.services.openrouter_service import OpenRouterService
from app.memory.simple_memory import SimpleMemory
from app.models.research import AgentState

logger = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self, faiss_service=None, reranker=None, arxiv_service=None, mcp_service=None):
        self.memory = SimpleMemory()
        self.openrouter = OpenRouterService()
        self.faiss_service = faiss_service
        self.reranker = reranker
        self.arxiv_service = arxiv_service
        self.mcp_service = mcp_service
        self.graph = self._create_research_graph()

    def _create_research_graph(self):
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("route_query", self._route_query)
        workflow.add_node("search_arxiv", self._search_arxiv)
        workflow.add_node("search_datagouv", self._search_datagouv)
        workflow.add_node("generate_answer", self._generate_answer)
        
        # Define edges
        workflow.add_edge(START, "route_query")
        
        # Conditional edge: route to arxiv or datagouv based on state["selected_source"]
        workflow.add_conditional_edges(
            "route_query",
            lambda state: state["selected_source"],
            {
                "arxiv": "search_arxiv",
                "datagouv": "search_datagouv"
            }
        )
        
        workflow.add_edge("search_arxiv", "generate_answer")
        workflow.add_edge("search_datagouv", "generate_answer")
        workflow.add_edge("generate_answer", END)
        
        return workflow.compile()

    # --- Nodes ---

    async def _route_query(self, state: AgentState) -> Dict[str, Any]:
        """Node: Use LLM to analyze the question and select the source."""
        question = state["question"]
        logger.info(f"Routing query: {question}")
        
        prompt = f"""Tu es un routeur de recherche intelligent.
Ta tâche est de déterminer la meilleure source de données pour répondre à la question suivante :
Question : "{question}"

Options de sources :
- "arxiv" : Si la question porte sur des articles de recherche scientifique, de la physique, des mathématiques, de l'informatique théorique ou de l'IA.
- "datagouv" : Si la question porte sur des statistiques publiques françaises, de l'administration, du budget, de l'écologie, des transports publics, ou de la démographie en France.

Réponds UNIQUEMENT par l'un de ces mots : "arxiv" ou "datagouv". Si le sujet ne correspond ni à l'un ni à l'autre, choisis par défaut celui qui s'en rapproche le plus, ou "arxiv" en cas de doute. Ne rajoute aucune ponctuation.
"""
        messages = [{"role": "user", "content": prompt}]
        response = await self.openrouter.create_chat_completion(messages)
        source = self.openrouter.extract_response_content(response).strip().lower()
        
        # Fallback sanitize
        if "datagouv" in source:
            selected = "datagouv"
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

    async def _search_datagouv(self, state: AgentState) -> Dict[str, Any]:
        """Node: Search Datagouv via MCP with SSE and create_react_agent."""
        question = state["question"]
        logger.info(f"Searching Data.gouv.fr (MCP) for: {question}")
        
        from app.core.config import settings
        from langgraph.prebuilt import create_react_agent
        from langchain_openai import ChatOpenAI
        
        content = []
        url = settings.MCP_SERVER
        
        if self.mcp_service:
            try:
                # 1. Utilisation du service HTTP Stateless de Data.gouv.fr
                tools = await self.mcp_service.get_langchain_tools(url)
                
                # 2. Si Data.Gouv a bien répondu (tools > 0)
                if tools:
                    logger.info(f"Data.gouv tools: {tools}")
                    # 3. Initialiser le ChatOpenAI vers l'endpoint (OpenRouter dans ce cas)
                    llm = ChatOpenAI(
                        base_url=settings.OPENROUTER_API_URL, 
                        api_key=settings.OPENROUTER_API_KEY, 
                        model="openai/gpt-4o-mini",
                        temperature=0.8
                    )
                    
                    # 4. Le create_react_agent gère l'orchestration des outils MCP nativement.
                    agent = create_react_agent(llm, tools)
                    
                    prompt = (
                        f"Tu es un agent de l'état travaillant avec les données de data.gouv.fr.\n"
                        f"Utilise tes outils (search_datasets, list_dataset_resources, query_resource_data, etc) "
                        f"pour rechercher les meilleures informations concernant cette requête : '{question}'.\n"
                        f"Génères en réponse un résumé structuré des statistiques ou du contenu des jeux de données trouvés."
                    )
                    
                    # 5. Exécution de l'agent
                    response = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
                    final_msg = response["messages"][-1].content
                    
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
                
        return {"crawled_content": content}

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
        messages = [{"role": "user", "content": prompt}]
        response = await self.openrouter.create_chat_completion(messages)
        answer = self.openrouter.extract_response_content(response)
        
        return {"answer": answer}

    async def stream_question(self, question: str, interests: List[str] = None, preferred_links: List[str] = None):
        """Main entry point for streaming: Execute graph and yield events."""
        initial_state = {
            "question": question,
            "interests": interests or [],
            "preferred_links": preferred_links or [],
            "keywords": [],
            "urls": [],
            "crawled_content": [],
            "selected_source": "",
            "answer": ""
        }
        
        import json
        yield json.dumps({"step": "start", "message": f"Reçu : '{question}'", "data": None})
        
        last_state = initial_state
        async for event in self.graph.astream(initial_state, stream_mode="updates"):
            for node_name, state_update in event.items():
                messages = {
                    "route_query": f"Analyse de la demande... Catégorie sélectionnée : {state_update.get('selected_source', 'inconnue').capitalize()}",
                    "search_arxiv": "Recherche sur ArXiv des articles scientifiques pertinents...",
                    "search_datagouv": "Appel de Data.gouv.fr (MCP) pour extraction des données publiques...",
                    "generate_answer": "Génération de la réponse finale à partir des sources..."
                }
                msg = messages.get(node_name, f"Étape achevée : {node_name}")
                yield json.dumps({"step": node_name, "message": msg, "data": None})
                last_state.update(state_update)
                
        # Final Event
        crawled = last_state.get('crawled_content', [])
        payload = {
            "answer": last_state.get("answer", ""),
            "sources": [{"title": c.get("title", f"Source {i+1}"), "url": c["url"]} for i, c in enumerate(crawled[:5])],
            "selected_source": last_state.get("selected_source", ""),
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
            "selected_source": "",
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
