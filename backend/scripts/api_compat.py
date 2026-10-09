#!/usr/bin/env python3
"""Fail when the API loses or renames something clients rely on (SYS-NFR-04, DES-API-03).

    python scripts/api_compat.py docs/openapi-baseline.yaml build/openapi.yaml

Compares an exported OpenAPI schema with the frozen baseline. Adding is allowed; these are
breaking: a removed or renamed path, method, response status, parameter, schema, property or
enum value; a changed type or format; a parameter or request field that has become required.
Run through `make schema`; `make baseline` freezes the current schema as the new baseline.
"""

import argparse
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

METHODS = ("get", "put", "post", "delete", "patch", "options", "head")
MAX_DEPTH = 6
Schema = Mapping[str, Any]


def _ref_name(value: object) -> str | None:
    if isinstance(value, Mapping) and isinstance(value.get("$ref"), str):
        return str(value["$ref"]).rsplit("/", 1)[-1]
    return None


class Comparison:
    def __init__(self, baseline: Schema, current: Schema) -> None:
        self.baseline, self.current = baseline, current
        self.old_schemas: Schema = baseline.get("components", {}).get("schemas", {})
        self.new_schemas: Schema = current.get("components", {}).get("schemas", {})
        self.found: list[str] = []

    def report(self, message: str) -> None:
        self.found.append(message)

    def schema(self, where: str, old: Schema, new: Schema, request: bool, depth: int = 0) -> None:
        old_ref, new_ref = _ref_name(old), _ref_name(new)
        if request and depth < MAX_DEPTH and (old_ref or new_ref):
            old = self.old_schemas.get(old_ref, {}) if old_ref else old
            new = self.new_schemas.get(new_ref, {}) if new_ref else new
            return self.schema(where, old, new, request, depth + 1)
        if old_ref or new_ref:
            if old_ref != new_ref:
                self.report(f"{where}: refers to {new_ref or 'an inline schema'}, was {old_ref}")
            return None
        for attribute in ("type", "format"):
            if attribute in old and old[attribute] != new.get(attribute):
                self.report(f"{where}: {attribute} {old[attribute]} became {new.get(attribute)}")
        if "enum" in old and "enum" in new:
            for value in old["enum"]:
                if value not in new["enum"]:
                    self.report(f"{where}: enum value {value!r} was removed")
        new_props: Schema = new.get("properties", {})
        for name, old_prop in old.get("properties", {}).items():
            if name in new_props:
                self.schema(f"{where}.{name}", old_prop, new_props[name], request, depth + 1)
            else:
                self.report(f"{where}: property {name} was removed or renamed")
        if "items" in old:
            self.schema(f"{where}[]", old["items"], new.get("items", {}), request, depth + 1)
        if request:
            for name in sorted(set(new.get("required", [])) - set(old.get("required", []))):
                self.report(f"{where}: {name} is now required")
        return None

    def operation(self, where: str, old: Schema, new: Schema) -> None:
        for status in old.get("responses", {}):
            if status not in new.get("responses", {}):
                self.report(f"{where}: response {status} was removed")
        old_params, new_params = _parameters(old), _parameters(new)
        for key in old_params:
            if key not in new_params:
                self.report(f"{where}: parameter {key[1]} was removed or renamed")
        for key, parameter in new_params.items():
            if key not in old_params and parameter.get("required"):
                self.report(f"{where}: new required parameter {key[1]}")
        old_body = _body(old)
        if old_body:
            self.schema(f"{where} request", old_body, _body(new), request=True)

    def run(self) -> list[str]:
        new_paths: Schema = self.current.get("paths", {})
        for path, old_item in self.baseline.get("paths", {}).items():
            new_item = new_paths.get(path)
            if new_item is None:
                self.report(f"path {path} was removed or renamed")
                continue
            for method in (m for m in METHODS if m in old_item):
                where = f"{method.upper()} {path}"
                if method in new_item:
                    self.operation(where, old_item[method], new_item[method])
                else:
                    self.report(f"{where} was removed")
        for name, old_schema in self.old_schemas.items():
            if name in self.new_schemas:
                self.schema(f"schema {name}", old_schema, self.new_schemas[name], request=False)
            else:
                self.report(f"schema {name} was removed or renamed")
        return self.found


def _parameters(operation: Schema) -> dict[tuple[str, str], Schema]:
    return {(p["in"], p["name"]): p for p in operation.get("parameters", []) if "name" in p}


def _body(operation: Schema) -> Schema:
    for media in operation.get("requestBody", {}).get("content", {}).values():
        schema: Schema = media.get("schema", {})
        return schema
    return {}


def breaking_changes(baseline: Schema, current: Schema) -> list[str]:
    return Comparison(baseline, current).run()


def load(path: Path) -> Schema:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise SystemExit(f"error: {path} is not an OpenAPI document")
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("current", type=Path)
    args = parser.parse_args()
    if not args.baseline.is_file():
        print(f"no baseline at {args.baseline}; run `make baseline` to freeze the schema")
        return 0
    problems = breaking_changes(load(args.baseline), load(args.current))
    for problem in problems:
        print(f"BREAKING {problem}")
    print(
        f"{len(problems)} breaking change(s)" if problems else "the API only gained; nothing lost"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
