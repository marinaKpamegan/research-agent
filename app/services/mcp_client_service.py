import logging
import httpx
import json
from typing import List, Any, Type
from pydantic import BaseModel, create_model, Field
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

class McpClientService:
    def __init__(self):
        pass

    async def get_langchain_tools(self, url: str) -> List[StructuredTool]:
        """
        Interroge le serveur MCP (FastMCP Stateless HTTP) pour récupérer la liste des outils,
        puis convertit chaque outil en un StructuredTool LangChain.
        """
        tools = []
        
        async with httpx.AsyncClient() as client:
            try:
                # Requête JSON-RPC sur le portail stateless
                resp = await client.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    },
                    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                    timeout=10.0
                )
                resp.raise_for_status()
                
                # FastMCP Stateless Streamable HTTP wraps the POST response inside an SSE message
                resp_text = resp.text
                data = {}
                for line in resp_text.splitlines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        break
                        
                mcp_tools = data.get("result", {}).get("tools", [])
                
                logger.info(f"MCP tools: {mcp_tools}")
                
                for mcp_tool in mcp_tools:
                    tool_name = mcp_tool.get("name")
                    tool_desc = mcp_tool.get("description", "")
                    input_schema = mcp_tool.get("inputSchema", {})
                    
                    # 1. Conversion du schéma JSON
                    pydantic_model = self._create_pydantic_model(tool_name, input_schema)
                    
                    # 2. Closure d'Appel HTTP POST JSON-RPC ("tools/call")
                    def create_closure(_name: str, _url: str):
                        async def func_wrapper(**kwargs) -> str:
                            # NETTOYAGE : Supprimer les arguments None pour éviter les erreurs de validation MCP
                            cleaned_args = {k: v for k, v in kwargs.items() if v is not None}
                            
                            async with httpx.AsyncClient() as inner_client:
                                try:
                                    call_resp = await inner_client.post(
                                        _url,
                                        headers={
                                            "Content-Type": "application/json",
                                            "Accept": "application/json, text/event-stream"
                                        },
                                        json={
                                            "jsonrpc": "2.0", 
                                            "id": 2, 
                                            "method": "tools/call", 
                                            "params": {"name": _name, "arguments": cleaned_args}
                                        },
                                        timeout=45.0
                                    )
                                    call_resp.raise_for_status()
                                    
                                    # FastMCP wraps the JSON in SSE payload
                                    call_data = {}
                                    for line in call_resp.text.splitlines():
                                        if line.startswith("data: "):
                                            call_data = json.loads(line[6:])
                                            break
                                    
                                    if "error" in call_data:
                                        return f"Error from Data.Gouv MCP: {call_data['error']}"
                                        
                                    result_content = call_data.get("result", {}).get("content", [])
                                    if not result_content:
                                        return "No result found for tool."
                                        
                                    return "\n".join([c.get("text", "") for c in result_content if "text" in c])
                                    
                                except Exception as e:
                                    return f"Failed to call MCP tool {_name}: {e}"

                        return func_wrapper

                    func_wrapper = create_closure(tool_name, url)
                    func_wrapper.__name__ = f"mcp_{tool_name}"
                    func_wrapper.__doc__ = tool_desc
                    
                    # 3. Création de l'outil LangChain natif
                    lc_tool = StructuredTool(
                        name=tool_name,
                        description=tool_desc,
                        func=None,
                        coroutine=func_wrapper,
                        args_schema=pydantic_model
                    )
                    tools.append(lc_tool)
                    
                logger.info(f"Dynamically loaded {len(tools)} LangChain MCP tools via Stateless HTTP.")
            except Exception as e:
                logger.error(f"Erreur d'initialisation MCP listTools: {e}")
                
        return tools

    def _create_pydantic_model(self, tool_name: str, json_schema: dict) -> Type[BaseModel]:
        """
        Génère dynamiquement une classe BaseModel (Pydantic) à partir d'un json-schema.
        """
        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])
        
        fields = {}
        for prop_name, prop_data in properties.items():
            prop_type_str = prop_data.get("type", "string")
            description = prop_data.get("description", "")
            
            type_mapping = {
                "string": str,
                "number": float,
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict
            }
            py_type = type_mapping.get(prop_type_str, Any)
            
            if prop_name in required:
                default_value = ...
            else:
                py_type = py_type | None
                default_value = None
            
            fields[prop_name] = (py_type, Field(default=default_value, description=description))
            
        return create_model(f"{tool_name}Schema", **fields)
