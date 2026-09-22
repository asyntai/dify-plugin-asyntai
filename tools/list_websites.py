from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.asyntai_api import AsyntaiError, get


class ListWebsitesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key", "")

        try:
            payload = get("/api/v1/websites/", api_key)
        except AsyntaiError as exc:
            yield self.create_text_message(str(exc))
            return

        websites = payload.get("websites") or []

        if not websites:
            yield self.create_text_message(
                "This account has no website yet. Add one at https://asyntai.com/dashboard/."
            )
            yield self.create_json_message({"count": 0, "websites": []})
            return

        lines = []
        for website in websites:
            mark = " (primary)" if website.get("is_primary") else ""
            lines.append(f"- {website.get('id')}: {website.get('domain')}{mark}")

        yield self.create_text_message("\n".join(lines))
        yield self.create_json_message({"count": len(websites), "websites": websites})
