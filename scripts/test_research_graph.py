import asyncio
import sys
import os
import logging

# Add project root to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.agents.research_agent import ResearchAgent

async def run_research(question: str):
    print(f"--- Running Research Agent (LangGraph) for: '{question}' ---")
    agent = ResearchAgent()
    
    try:
        # handle_question now returns a structured dict (from ResearchResult)
        result = await agent.handle_question(question)
        print(f"\nSummary of results:")
        print(f"- Question: {result['question']}")
        print(f"- Keywords: {result['keywords']}")
        print(f"- URLs found: {len(result['urls'])}")
        print(f"- Content items: {len(result['content'])}")
        
        if result['content']:
            print(f"\nFirst content preview: {result['content'][0]['url']}")
            print(f"Score: {result['content'][0]['score']:.2f}")
        
        print("\nWorkflow completed successfully!")
        
    except Exception as e:
        print(f"\nError running agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    question = "What are the latest breakthroughs in room-temperature superconductivity in 2024?"
    asyncio.run(run_research(question))
