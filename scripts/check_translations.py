"""Check bundled translations and version consistency without Home Assistant."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "meteoswiss"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate translation key: {key}")
        result[key] = value
    return result


def flatten(data, prefix=""):
    result = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten(value, path))
        elif isinstance(value, str) and value.strip() and "[%key:" not in value:
            result[path] = value
        else:
            raise ValueError(f"Missing, invalid or unresolved translation: {path}")
    return result


def validate():
    english = None
    for language in ("en", "de", "fr", "it"):
        path = COMPONENT / "translations" / f"{language}.json"
        catalogue = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=unique_object
        )
        for category in ("config", "options"):
            for step, form in catalogue[category]["step"].items():
                fields = set(form.get("data", {}))
                help_fields = set(form.get("data_description", {}))
                if fields != help_fields:
                    raise ValueError(
                        f"{language}: {category}.{step} help/field mismatch: "
                        f"missing={fields - help_fields}, extra={help_fields - fields}"
                    )
        current = flatten(catalogue)
        if english is None:
            english = current
        elif set(current) != set(english):
            raise ValueError(
                f"{language}: missing={set(english) - set(current)}, extra={set(current) - set(english)}"
            )
    strings = flatten(
        json.loads(
            (COMPONENT / "strings.json").read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
        )
    )
    if strings != english:
        raise ValueError("strings.json and English translations differ")
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    version = next(
        ast.literal_eval(node.value)
        for node in ast.parse((COMPONENT / "version.py").read_text()).body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        )
    )
    if manifest["version"] != version:
        raise ValueError("Manifest and module versions differ")
    print(
        f"Four complete translation catalogues ({len(english)} keys each); version {version}."
    )


if __name__ == "__main__":
    validate()
