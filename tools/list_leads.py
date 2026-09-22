from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.asyntai_api import AsyntaiError, get


class ListLeadsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key", "")

        try:
            payload = get(
                "/api/v1/leads/",
                api_key,
                {
                    "limit": tool_parameters.get("limit") or 20,
                    "email": tool_parameters.get("email"),
                    "since": tool_parameters.get("since"),
                    "website_id": tool_parameters.get("website_id"),
                },
            )
        except AsyntaiError as exc:
            yield self.create_text_message(str(exc))
            return

        leads = payload.get("leads") or []

        if not leads:
            yield self.create_text_message("No leads match this search.")
            yield self.create_json_message({"count": 0, "leads": []})
            return

        lines = [f"{len(leads)} lead(s):"]
        for lead in leads:
            # An agent reads this text, so each line carries the contact first
            # and the page second, which is the order a person needs them in.
            contact = lead.get("email") or lead.get("phone") or "no contact"
            page = lead.get("page_url") or "unknown page"
            started = (lead.get("started_at") or "")[:10]
            lines.append(f"- {contact} on {page} ({started})")

        yield self.create_text_message("\n".join(lines))
        yield self.create_json_message({"count": len(leads), "leads": leads})
