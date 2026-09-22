from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.asyntai_api import AsyntaiError, post


class AskWebsiteTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        question = (tool_parameters.get("question") or "").strip()
        if not question:
            yield self.create_text_message("Write a question first.")
            return

        api_key = self.runtime.credentials.get("api_key", "")

        try:
            payload = post(
                "/api/v1/chat/",
                api_key,
                {
                    "message": question,
                    "website_id": tool_parameters.get("website_id"),
                    "session_id": tool_parameters.get("session_id"),
                },
            )
        except AsyntaiError as exc:
            yield self.create_text_message(str(exc))
            return

        answer = payload.get("response") or ""

        # The text message is what an agent reads back. The JSON message carries
        # the session id, so a workflow can keep the same conversation going,
        # and the AI disclosure sentence the EU AI Act asks for on the first
        # reply of a conversation.
        yield self.create_text_message(answer)
        yield self.create_json_message(
            {
                "answer": answer,
                "session_id": payload.get("session_id"),
                "ai_disclosure": payload.get("ai_disclosure", ""),
            }
        )
