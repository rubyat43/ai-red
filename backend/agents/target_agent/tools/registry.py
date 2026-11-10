# agents/target_agent/tools/registry.py
# Purpose: Registry of all available tools for the target agent.

from typing import Dict
from agents.target_agent.tools.base_tool import BaseTool
from agents.target_agent.tools.search_docs import SearchDocsTool
from agents.target_agent.tools.read_file import ReadFileTool
from agents.target_agent.tools.send_email import SendEmailTool
from agents.target_agent.tools.run_sql import RunSqlTool


def get_default_tool_registry() -> Dict[str, BaseTool]:
    """
    Returns a dictionary of all standard sandboxed tools.
    """
    tools = [
        SearchDocsTool(),
        ReadFileTool(),
        SendEmailTool(),
        RunSqlTool(),
    ]
    return {tool.name: tool for tool in tools}
