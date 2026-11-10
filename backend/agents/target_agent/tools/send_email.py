# agents/target_agent/tools/send_email.py
# Purpose: FAKE email sender tool. Only writes outbound messages to an in-memory audit log.

from typing import Dict, Any, List
from agents.target_agent.tools.base_tool import BaseTool


class SendEmailTool(BaseTool):
    name = "send_email"
    description = "Send an email message (sandboxed simulation, writes to memory log)."
    required_permission = "user"

    def __init__(self):
        self.sent_log: List[Dict[str, str]] = []

    def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        recipient = str(args.get("to", ""))
        subject = str(args.get("subject", ""))
        body = str(args.get("body", ""))

        record = {
            "to": recipient,
            "subject": subject,
            "body": body,
        }
        self.sent_log.append(record)

        return {
            "status": "success",
            "message": f"Simulated email sent to {recipient}",
            "log_count": len(self.sent_log),
        }
