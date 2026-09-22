from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.asyntai_api import AsyntaiError, get

SPEAKER = {"user": "Visitor", "assistant": "Assistant"}


class GetConversationTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        session_id = (tool_parameters.get("session_id") or "").strip()
        if not session_id:
            yield self.create_text_message("Give the session ID of the chat.")
            return

        api_key = self.runtime.credentials.get("api_key", "")

        try:
            payload = get(
                "/api/v1/conversations/",
                api_key,
                {
                    "session_id": session_id,
                    "limit": tool_parameters.get("limit") or 50,
                },
            )
        except AsyntaiError as exc:
            yield self.create_text_message(str(exc))
            return

        messages = payload.get("messages") or []

        if not messages:
            yield self.create_text_message(f"No messages found for session {session_id}.")
            yield self.create_json_message({"session_id": session_id, "messages": []})
            return

        lines = []
        for message in messages:
            who = SPEAKER.get(message.get("role"), message.get("role") or "?")
            lines.append(f"{who}: {message.get('content') or ''}")

        yield self.create_text_message("\n".join(lines))
        yield self.create_json_message(
            {"session_id": session_id, "messages": messages}
        )
