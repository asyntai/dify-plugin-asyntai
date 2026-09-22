from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from utils.asyntai_api import AsyntaiError, get


class AsyntaiProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """Ask Asyntai who this key belongs to.

        /api/v1/account/ is the cheapest endpoint that needs both a valid key
        and a plan with API access, so one call proves the key works.
        """
        try:
            get("/api/v1/account/", credentials.get("api_key", ""))
        except AsyntaiError as exc:
            raise ToolProviderCredentialValidationError(str(exc))
        except Exception as exc:
            raise ToolProviderCredentialValidationError(str(exc))
