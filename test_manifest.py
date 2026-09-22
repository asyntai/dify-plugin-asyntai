"""Check every YAML file against the models Dify itself parses them with.

Dify reads these files when the plugin is installed. If a field is missing or
misspelled, the install fails there. This script fails here instead.

    .venv/Scripts/python.exe test_manifest.py
"""

import io
import os
import sys

import yaml
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dify_plugin.entities.tool import (  # noqa: E402
    ToolConfiguration,
    ToolProviderConfiguration,
)

HERE = os.path.dirname(os.path.abspath(__file__))

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


def load(relative):
    with io.open(os.path.join(HERE, relative), encoding="utf-8") as handle:
        return yaml.safe_load(handle)


print("Manifest")
manifest = load("manifest.yaml")
check("version is set", bool(manifest.get("version")), manifest.get("version"))
check("author is asyntai", manifest.get("author") == "asyntai", manifest.get("author"))
check("name is asyntai", manifest.get("name") == "asyntai", manifest.get("name"))
check("icon file exists", os.path.exists(os.path.join(HERE, "_assets", manifest["icon"])))
check("privacy file exists", os.path.exists(os.path.join(HERE, manifest["privacy"])))
check(
    "privacy has no placeholder",
    "Please fill in" not in io.open(os.path.join(HERE, manifest["privacy"]), encoding="utf-8").read(),
)
check(
    "readme has no placeholder",
    "Replace the placeholder" not in io.open(os.path.join(HERE, "README.md"), encoding="utf-8").read(),
)
readme = io.open(os.path.join(HERE, "README.md"), encoding="utf-8").read()
check(
    "readme is English only",
    all(ord(c) < 0x2E80 for c in readme),
    "a Chinese character would fail the review",
)
check("tool permission is on", manifest["resource"]["permission"]["tool"]["enabled"])
check("minimum dify version is set", bool(manifest["meta"].get("minimum_dify_version")))

print("\nProvider")
provider_raw = load("provider/asyntai.yaml")
try:
    provider = ToolProviderConfiguration(**provider_raw)
    check("provider yaml parses", True)
except ValidationError as exc:
    check("provider yaml parses", False, str(exc))
    provider = None

if provider:
    names = [c.name for c in provider.credentials_schema]
    check("asks for an api_key", names == ["api_key"], names)
    field = provider.credentials_schema[0]
    check("the api_key is a secret field", field.type.value == "secret-input", field.type)
    check("the api_key is required", field.required is True)
    check("the api_key has help text", bool(field.help and field.help.en_us))
    check("the provider has 6 tools", len(provider_raw["tools"]) == 6, provider_raw["tools"])

print("\nTools")
expected = {
    "ask_website",
    "add_page",
    "add_text",
    "list_leads",
    "get_conversation",
    "list_websites",
}
found = set()
for relative in provider_raw["tools"]:
    raw = load(relative)
    label = relative
    try:
        tool = ToolConfiguration(**raw)
        check(f"{label} parses", True)
    except ValidationError as exc:
        check(f"{label} parses", False, str(exc))
        continue

    found.add(tool.identity.name)
    source = raw["extra"]["python"]["source"]
    check(f"{label} source exists", os.path.exists(os.path.join(HERE, source)), source)
    check(
        f"{label} has an llm description",
        bool(tool.description.llm and len(tool.description.llm) > 20),
    )
    for parameter in tool.parameters:
        check(
            f"{label}:{parameter.name} has a form",
            parameter.form is not None,
        )
        check(
            f"{label}:{parameter.name} has an en_US label",
            bool(parameter.label and parameter.label.en_us),
        )

check("every expected tool is present", found == expected, found ^ expected)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
