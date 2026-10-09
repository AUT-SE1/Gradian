import copy
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

import api_compat
import yaml
from covers import covers

ROOT = Path(__file__).resolve().parents[2]
JSON = "application/json"
Edit = Callable[[dict[str, Any]], object]


def spec() -> dict[str, Any]:
    return {
        "paths": {
            "/api/v1/me": {
                "get": {
                    "parameters": [{"in": "query", "name": "q", "schema": {"type": "string"}}],
                    "responses": {"200": {}, "401": {}},
                },
                "patch": {
                    "requestBody": {
                        "content": {JSON: {"schema": {"$ref": "#/components/schemas/Update"}}}
                    },
                    "responses": {"200": {}},
                },
            }
        },
        "components": {
            "schemas": {
                "Me": {
                    "type": "object",
                    "properties": {
                        "sub": {"type": "string", "format": "uuid"},
                        "role": {"type": "string", "enum": ["student", "admin"]},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "Update": {"type": "object", "properties": {"bio": {"type": "string"}}},
            }
        },
    }


def me(doc: dict[str, Any]) -> dict[str, Any]:
    properties: dict[str, Any] = doc["components"]["schemas"]["Me"]["properties"]
    return properties


def get(doc: dict[str, Any]) -> dict[str, Any]:
    operation: dict[str, Any] = doc["paths"]["/api/v1/me"]["get"]
    return operation


def changed(edit: Edit) -> list[str]:
    current = spec()
    edit(current)
    return api_compat.breaking_changes(spec(), current)


@covers("SYS-NFR-04")
class ApiCompatTests(unittest.TestCase):
    def test_the_same_schema_has_no_breaking_change(self) -> None:
        self.assertEqual(api_compat.breaking_changes(spec(), spec()), [])

    def test_adding_things_is_allowed(self) -> None:
        def add(doc: dict[str, Any]) -> None:
            doc["paths"]["/api/v1/new"] = {"get": {"responses": {"200": {}}}}
            get(doc)["responses"]["429"] = {}
            get(doc)["parameters"].append({"in": "query", "name": "x", "schema": {}})
            me(doc)["avatar"] = {"type": "string"}
            me(doc)["role"]["enum"].append("professor")
            doc["components"]["schemas"]["Brand"] = {"type": "object"}
            doc["components"]["schemas"]["Me"]["required"] = ["sub"]

        self.assertEqual(changed(add), [])

    def test_losing_or_renaming_something_is_breaking(self) -> None:
        def rename_path(doc: dict[str, Any]) -> None:
            doc["paths"]["/api/v1/profile"] = doc["paths"].pop("/api/v1/me")

        def rename_property(doc: dict[str, Any]) -> None:
            me(doc)["subject"] = me(doc).pop("sub")

        edits: dict[str, Edit] = {
            "a removed path": lambda d: d["paths"].pop("/api/v1/me"),
            "a renamed path": rename_path,
            "a removed method": lambda d: d["paths"]["/api/v1/me"].pop("patch"),
            "a removed response": lambda d: get(d)["responses"].pop("401"),
            "a removed parameter": lambda d: get(d).update(parameters=[]),
            "a removed schema": lambda d: d["components"]["schemas"].pop("Me"),
            "a removed property": lambda d: me(d).pop("sub"),
            "a renamed property": rename_property,
            "a changed type": lambda d: me(d)["sub"].update(type="integer"),
            "a changed format": lambda d: me(d)["sub"].update(format="date"),
            "a removed enum value": lambda d: me(d)["role"]["enum"].remove("admin"),
            "a changed array item type": lambda d: me(d)["tags"].update(items={"type": "integer"}),
        }
        for label, edit in edits.items():
            with self.subTest(label):
                self.assertTrue(changed(edit), f"{label} was not reported")

    def test_a_new_required_parameter_is_breaking(self) -> None:
        problems = changed(
            lambda d: get(d)["parameters"].append(
                {"in": "query", "name": "must", "required": True, "schema": {"type": "string"}}
            )
        )
        self.assertEqual(problems, ["GET /api/v1/me: new required parameter must"])

    def test_a_newly_required_request_field_is_breaking_even_behind_a_reference(self) -> None:
        problems = changed(lambda d: d["components"]["schemas"]["Update"].update(required=["bio"]))
        self.assertEqual(problems, ["PATCH /api/v1/me request: bio is now required"])

    def test_a_request_field_that_disappears_behind_a_reference_is_breaking(self) -> None:
        problems = changed(lambda d: d["components"]["schemas"]["Update"]["properties"].pop("bio"))
        self.assertTrue(any("request" in problem for problem in problems))

    def test_a_newly_required_output_field_is_not_breaking(self) -> None:
        self.assertEqual(
            changed(lambda d: d["components"]["schemas"]["Me"].update(required=["sub"])), []
        )

    def test_the_baseline_is_not_modified_by_the_comparison(self) -> None:
        baseline, current = spec(), copy.deepcopy(spec())
        api_compat.breaking_changes(baseline, current)
        self.assertEqual(baseline, spec())

    def test_the_committed_baseline_is_an_openapi_document_when_it_exists(self) -> None:
        path = ROOT / "docs" / "openapi-baseline.yaml"
        if path.is_file():
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertIn("/api/v1/me", document["paths"])
