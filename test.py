import asyncio
import logging
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# Config logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Loading Environment variables
load_dotenv()

# MCP URL (Transport: Streamable HTTP)
MCP_URL = "https://mcp.data.gouv.fr/mcp"

# Add your API key in .env file. You can get one here: https://aistudio.google.com/api-keys
# GOOGLE_API_KEY=your_api_key

SYSTEM_PROMPT = """
Tu es un expert Data Analyst spécialisé sur Data.gouv.fr.
Règle absolue : suis STRICTEMENT cette méthode en entonnoir :

1. DÉCOUVERTE : Recherche des datasets avec 'search_datasets'. Trouve l'ID le plus pertinent.
2. EXPLORATION : Utilise 'get_dataset_info' avec cet ID pour identifier les fichiers disponibles.
3. EXTRACTION : Utilise 'query_resource_data' sur les fichiers CSV/JSON pour obtenir les vraies données.
4. FINALISATION : Ne retourne jamais de métadonnées. Retourne toujours une réponse factuelle avec des chiffres.
"""

async def main():
    logger.info(f"Connexion au serveur MCP : {MCP_URL}")
    
    try:
        # Utilisation de streamable_http_client avec déballage des 3 valeurs (read, write, session_id_getter)
        async with streamable_http_client(MCP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                # Initialization of the MCP session
                await session.initialize()
                
                # Conversion MCP tools into LangChain tools
                tools = await load_mcp_tools(session)
                # logger.info(f"✅ {len(tools)} outils chargés : {[t.name for t in tools]}")
                print(f"\n\n\n ===========>  {len(tools)} tools available: {[t.name for t in tools]}\n\n\n")

                # Initialization of the Gemini 2.5 Flash model
                model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
                
                # Creation of the ReAct agent with LangGraph (argument 'prompt' for the system)
                agent = create_react_agent(model, tools=tools, prompt=SYSTEM_PROMPT)

                query = "Combien y a-t-il d'écoles primaires en France ?"
                logger.info(f"Question : {query}")
                
                # Invocation of the agent
                response = await agent.ainvoke({
                    "messages": [("user", query)]
                })

                # Displaying the final result (extracting only the text)
                final_message = response["messages"][-1]
                final_text = final_message.content
                
                if isinstance(final_text, list):
                    # If it's a list of blocks (Gemini format), merge the text parts
                    final_text = "".join([block.get("text", "") for block in final_text if isinstance(block, dict) and block.get("type") == "text"])

                print("\n" + "="*50)
                print("FINAL RESPONSE :")
                print(final_text)
                print("="*50 + "\n")
                
    except Exception:
        logger.exception("Error during execution")

if __name__ == "__main__":
    asyncio.run(main())