from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.asyntai_api import AsyntaiError, post


class AddTextTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        title = (tool_parameters.get("title") or "").strip()
        content = (tool_parameters.get("content") or "").strip()

        if not title:
            yield self.create_text_message("Give the note a title.")
            return
        if len(content) < 10:
            yield self.create_text_message("Write at least 10 characters of text.")
            return

        api_key = self.runtime.credentials.get("api_key", "")

        try:
            payload = post(
                "/api/v1/knowledge/text/",
                api_key,
                {
                    "title": title,
                    "content": content,
                    "website_id": tool_parameters.get("website_id"),
                },
            )
        except AsyntaiError as exc:
            yield self.create_text_message(str(exc))
            return

        chunks = payload.get("chunks_created", 0)

        yield self.create_text_message(
            f'Added "{title}" to the knowledge base, in {chunks} parts.'
        )
        yield self.create_json_message(
            {
                "id": payload.get("id"),
                "title": payload.get("title", title),
                "chunks_created": chunks,
            }
        )
