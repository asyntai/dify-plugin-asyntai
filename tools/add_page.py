from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.asyntai_api import AsyntaiError, post


class AddPageTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        url = (tool_parameters.get("url") or "").strip()
        if not url:
            yield self.create_text_message("Give the address of the page to add.")
            return

        api_key = self.runtime.credentials.get("api_key", "")

        try:
            payload = post(
                "/api/v1/knowledge/url/",
                api_key,
                {"url": url, "website_id": tool_parameters.get("website_id")},
            )
        except AsyntaiError as exc:
            yield self.create_text_message(str(exc))
            return

        title = payload.get("title") or url
        chunks = payload.get("chunks_created", 0)

        yield self.create_text_message(
            f'Added "{title}" to the knowledge base, in {chunks} parts.'
        )
        yield self.create_json_message(
            {
                "id": payload.get("id"),
                "title": title,
                "url": payload.get("url", url),
                "chunks_created": chunks,
            }
        )
