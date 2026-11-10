# agents/target_agent/tools/search_docs.py
# Purpose: Sandboxed document search tool over an in-memory knowledge base.

from typing import Dict, Any, List
from agents.target_agent.tools.base_tool import BaseTool

MOCK_DOCUMENTS = [
    {
        "id": "doc-1",
        "title": "Refund Policy",
        "content": "Customers can request a refund within 30 days of purchase with a valid receipt.",
    },
    {
        "id": "doc-2",
        "title": "Service Level Agreement",
        "content": "Our cloud platform guarantees 99.9% uptime for enterprise tier customers.",
    },
    {
        "id": "doc-3",
        "title": "Password Reset Procedures",
        "content": "Users must initiate password resets via official email verification links.",
    },
]


class SearchDocsTool(BaseTool):
    name = "search_docs"
    description = "Search company documentation and guidelines for a given query."
    required_permission = "user"

    def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search mock documents by query keyword.
        """
        query = str(args.get("query", "")).lower()
        results: List[Dict[str, str]] = []

        for doc in MOCK_DOCUMENTS:
            if query in doc["title"].lower() or query in doc["content"].lower():
                results.append(doc)

        return {
            "status": "success",
            "matches_found": len(results),
            "results": results if results else "No matching documents found.",
        }
