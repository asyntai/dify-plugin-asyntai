"""End to end test for the Asyntai Dify plugin.

Runs every tool through the real Dify SDK against a real Asyntai API. Point
ASYNTAI_TEST_BASE at a local rig, or leave it out to test against asyntai.com.

    .venv/Scripts/python.exe test_plugin.py

The script prints one line per check and exits non-zero if any check fails.
"""

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import asyntai_api  # noqa: E402

BASE = os.environ.get("ASYNTAI_TEST_BASE", "").rstrip("/")
if BASE:
    asyntai_api.BASE_URL = BASE

API_KEY = os.environ.get("ASYNTAI_TEST_KEY", "")
if not API_KEY:
    sys.exit("Set ASYNTAI_TEST_KEY to the API key of the test account.")

from dify_plugin.errors.tool import ToolProviderCredentialValidationError  # noqa: E402

from provider.asyntai import AsyntaiProvider  # noqa: E402
from tools.add_page import AddPageTool  # noqa: E402
from tools.add_text import AddTextTool  # noqa: E402
from tools.ask_website import AskWebsiteTool  # noqa: E402
from tools.get_conversation import GetConversationTool  # noqa: E402
from tools.list_leads import ListLeadsTool  # noqa: E402
from tools.list_websites import ListWebsitesTool  # noqa: E402

CREDENTIALS = {"api_key": API_KEY}

passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def run(tool_class, parameters):
    """Run one tool and split its messages into text and json."""
    tool = tool_class.from_credentials(CREDENTIALS, user_id="test-user")
    texts, jsons = [], []
    for message in tool.invoke(parameters):
        kind = message.type.value if hasattr(message.type, "value") else str(message.type)
        if kind == "text":
            texts.append(message.message.text)
        elif kind == "json":
            jsons.append(message.message.json_object)
    return texts, jsons


def section(title):
    print(f"\n{title}")


def safe(text):
    """The Windows console is cp1252, and answers carry other characters."""
    return str(text).encode("ascii", "replace").decode("ascii")


# ---------------------------------------------------------------- provider
section("Provider credentials")
try:
    AsyntaiProvider().validate_credentials(CREDENTIALS)
    check("a good API key is accepted", True)
except Exception as exc:
    check("a good API key is accepted", False, repr(exc))

try:
    AsyntaiProvider().validate_credentials({"api_key": "obviously-wrong-key"})
    check("a bad API key is refused", False, "no error was raised")
except ToolProviderCredentialValidationError as exc:
    check("a bad API key is refused", "API key" in str(exc), str(exc))
except Exception as exc:
    check("a bad API key is refused", False, repr(exc))

# ---------------------------------------------------------- list websites
section("List websites")
texts, jsons = run(ListWebsitesTool, {})
check("returns a text list", bool(texts) and "-" in texts[0], texts)
check("returns json with a count", bool(jsons) and jsons[0].get("count", 0) > 0, jsons)

websites = jsons[0]["websites"] if jsons else []
primary = next((w for w in websites if w.get("is_primary")), websites[0] if websites else {})
website_id = str(primary.get("id", ""))
check("marks the primary website", "(primary)" in texts[0], texts)
print(f"  ..    primary website id = {website_id}")

# ---------------------------------------------------------------- add text
section("Add a note to the knowledge base")
texts, jsons = run(
    AddTextTool,
    {
        "title": "Dify plugin test note",
        "content": (
            "The Dify plugin test note exists to prove the tool works. "
            "The secret answer is BLUE PELICAN."
        ),
        "website_id": website_id,
    },
)
check("confirms the note was added", bool(texts) and "knowledge base" in texts[0], texts)
check("returns an id", bool(jsons) and bool(jsons[0].get("id")), jsons)

texts, jsons = run(AddTextTool, {"title": "x", "content": "short"})
check("refuses a text under 10 characters", "10 characters" in (texts[0] if texts else ""), texts)

texts, jsons = run(AddTextTool, {"title": "", "content": "long enough content here"})
check("refuses an empty title", "title" in (texts[0] if texts else "").lower(), texts)

# ---------------------------------------------------------------- add page
section("Add a page to the knowledge base")
texts, jsons = run(AddPageTool, {"url": "https://example.com/", "website_id": website_id})
check("confirms the page was added", bool(texts) and "knowledge base" in texts[0], texts)
check("returns chunks_created", bool(jsons) and "chunks_created" in jsons[0], jsons)

texts, jsons = run(AddPageTool, {"url": ""})
check("refuses an empty URL", "address" in (texts[0] if texts else "").lower(), texts)

# ------------------------------------------------------------- list leads
section("List leads")
texts, jsons = run(ListLeadsTool, {"limit": 10})
check("returns a text list", bool(texts), texts)
check("returns json with leads", bool(jsons) and "leads" in jsons[0], jsons)

leads = jsons[0].get("leads", []) if jsons else []
session_id = leads[0].get("session_id") if leads else ""
print(f"  ..    first lead session = {safe(session_id)}")

texts, jsons = run(ListLeadsTool, {"limit": 10, "email": "nobody-at-all@example.invalid"})
check("an unknown address returns nothing", "No leads" in (texts[0] if texts else ""), texts)

# -------------------------------------------------------- get conversation
section("Read a chat")
if session_id:
    texts, jsons = run(GetConversationTool, {"session_id": session_id})
    check("returns the messages", bool(texts) and ":" in texts[0], texts)
    check("returns json messages", bool(jsons) and bool(jsons[0].get("messages")), jsons)
    check(
        "names the speakers",
        "Visitor:" in texts[0] or "Assistant:" in texts[0],
        texts,
    )
else:
    check("returns the messages", False, "no lead to read")

texts, jsons = run(GetConversationTool, {"session_id": ""})
check("refuses an empty session ID", "session ID" in (texts[0] if texts else ""), texts)

# ----------------------------------------------------------- ask the website
section("Ask the website")
texts, jsons = run(
    AskWebsiteTool,
    {"question": "What is the secret answer in the Dify plugin test note?", "website_id": website_id},
)
check("returns an answer", bool(texts) and len(texts[0]) > 0, texts)
check("returns a session id", bool(jsons) and bool(jsons[0].get("session_id")), jsons)
if texts:
    print(f"  ..    answer = {safe(texts[0][:300])}")

texts, jsons = run(AskWebsiteTool, {"question": "  "})
check("refuses an empty question", "question" in (texts[0] if texts else "").lower(), texts)

# ------------------------------------------------------------ bad API key
section("A wrong API key inside a tool")
tool = ListWebsitesTool.from_credentials({"api_key": "wrong"}, user_id="test-user")
messages = list(tool.invoke({}))
text = messages[0].message.text if messages else ""
check("says the key was rejected", "API key" in text, safe(text))

# --------------------------------------------------------------------- end
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
