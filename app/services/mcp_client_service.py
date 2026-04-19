import logging
import asyncio
from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class McpClientService:
    def __init__(self):
        # We assume `datagouv-mcp` is available in the environment path or the active virtual environment
        self.server_params = StdioServerParameters(
            command="datagouv-mcp",
            args=[],
            env=None
        )

    async def _call_tool(self, tool_name: str, arguments: dict) -> Any:
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    return result
        except Exception as e:
            logger.error(f"Error calling MCP Tool {tool_name}: {e}")
            return None

    async def query_datagouv(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a static pipeline on Data.gouv.fr via MCP:
        1. Search datasets using the query.
        2. If found, list resources of the top dataset.
        3. If resources available, query the first tabular resource for data.
        """
        logger.info(f"Querying Datagouv-MCP for: {query}")
        
        # 1. Search Datasets
        search_res = await self._call_tool("search_datasets", {"query": query, "page_size": 1})
        if not search_res or not search_res.content:
            logger.info("No datasets found.")
            return []
            
        # Parse text content from MCP result
        # Assuming content is TextContent, we just need to get the actual JSON or string out.
        search_text = search_res.content[0].text if search_res.content else ""
        
        import json
        try:
            datasets = json.loads(search_text)
            if not datasets or not isinstance(datasets, list):
                return []
            dataset_id = datasets[0].get("id")
        except Exception:
            # Fallback if the output from MCP is different
            logger.error(f"Failed to parse dataset search response: {search_text}")
            return []

        if not dataset_id:
            return []

        logger.info(f"Top dataset found: {dataset_id}")

        # 2. List Resources
        res_info = await self._call_tool("list_dataset_resources", {"dataset_id": dataset_id})
        if not res_info or not res_info.content:
            return []

        res_text = res_info.content[0].text
        try:
            resources = json.loads(res_text)
        except Exception:
             logger.error(f"Failed to parse resources response: {res_text}")
             return []
             
        # Find a resource that is likely tabular (CSV)
        tabular_res = next((r for r in resources if r.get("format", "").upper() in ["CSV", "XLS", "XLSX"]), None)
        if not tabular_res:
            logger.info("No tabular resource found in dataset.")
            # We return dataset metadata as fallback context
            return [{"title": datasets[0].get("title"), "description": datasets[0].get("description", ""), "url": datasets[0].get("page")}]

        resource_id = tabular_res.get("id")
        logger.info(f"Querying Resource Data: {resource_id}")

        # 3. Query Resource Data (get first page)
        data_res = await self._call_tool("query_resource_data", {"resource_id": resource_id, "page_size": 20})
        if not data_res or not data_res.content:
            return []
            
        data_text = data_res.content[0].text
        
        return [{
            "title": datasets[0].get("title", "Dataset"),
            "url": datasets[0].get("page", ""),
            "content": f"Resource info: {tabular_res.get('title')}\nData Sample:\n{data_text}",
            "score": 1.0 # arbitrary
        }]
