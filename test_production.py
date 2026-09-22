"""Read-only check of the Asyntai Dify plugin against the real asyntai.com.

The write tools (add_page, add_text) are proved by test_plugin.py on the test
rig. This script leaves no new knowledge base item on a live account.

    set ASYNTAI_TEST_KEY=...  &&  .venv/Scripts/python.exe test_production.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_KEY = os.environ.get("ASYNTAI_TEST_KEY", "")
if not API_KEY:
    sys.exit("Set ASYNTAI_TEST_KEY.")

from dify_plugin.errors.tool import ToolProviderCredentialValidationError  # noqa: E402

from provider.asyntai import AsyntaiProvider  # noqa: E402
from tools.ask_website import AskWebsiteTool  # noqa: E402
from tools.get_conversation import GetConversationTool  # noqa: E402
from tools.list_leads import ListLeadsTool  # noqa: E402
from tools.list_websites import ListWebsitesTool  # noqa: E402

CREDENTIALS = {"api_key": API_KEY}
passed = failed = 0


def safe(text):
    return str(text).encode("ascii", "replace").decode("ascii")


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {safe(detail)}")


def run(tool_class, parameters):
    tool = tool_class.from_credentials(CREDENTIALS, user_id="prod-check")
    texts, jsons = [], []
    for message in tool.invoke(parameters):
        kind = message.type.value if hasattr(message.type, "value") else str(message.type)
        if kind == "text":
            texts.append(message.message.text)
        elif kind == "json":
            jsons.append(message.message.json_object)
    return texts, jsons


print("Provider")
try:
    AsyntaiProvider().validate_credentials(CREDENTIALS)
    check("the live API key is accepted", True)
except ToolProviderCredentialValidationError as exc:
    check("the live API key is accepted", False, exc)

print("\nList websites")
texts, jsons = run(ListWebsitesTool, {})
sites = jsons[0].get("websites", []) if jsons else []
check("returns at least one website", len(sites) > 0, texts)
primary = next((s for s in sites if s.get("is_primary")), sites[0] if sites else {})
print(f"  ..    {len(sites)} website(s); primary = {safe(primary.get('domain'))}")

print("\nList leads")
texts, jsons = run(ListLeadsTool, {"limit": 5})
leads = jsons[0].get("leads", []) if jsons else []
check("the call succeeds", bool(jsons), texts)
print(f"  ..    {len(leads)} lead(s) returned")

session_id = leads[0].get("session_id") if leads else ""

print("\nRead a chat")
if session_id:
    texts, jsons = run(GetConversationTool, {"session_id": session_id, "limit": 6})
    messages = jsons[0].get("messages", []) if jsons else []
    check("returns messages", len(messages) > 0, texts)
    print(f"  ..    {len(messages)} message(s) in the newest lead's chat")
else:
    print("  ..    no lead on this account, nothing to read")

print("\nAsk the website")
texts, jsons = run(AskWebsiteTool, {"question": "What does this company do?"})
answer = texts[0] if texts else ""
check("returns a real answer", len(answer) > 40, answer)
check("returns a session id", bool(jsons) and bool(jsons[0].get("session_id")), jsons)
print(f"  ..    answer = {safe(answer[:280])}")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
