from pathlib import Path

import yaml


def schema_text(catalog_path: str = "catalog.yaml") -> str:
    """Describes the views in plain text, for the model's system prompt."""
    catalog = yaml.safe_load(Path(catalog_path).read_text(encoding="utf-8"))
    lines = ["Views you can query:"]
    for name, view in catalog["views"].items():
        lines.append(f"\n{name}({', '.join(view['columns'])}): {view['description']}")
        for column, spec in view["columns"].items():
            lines.append(f"  {column}: {spec['description']}")
    lines.append("\nHow the views join:")
    lines.extend(f"  {join}" for join in catalog["joins"])
    return "\n".join(lines)


if __name__ == "__main__":
    print(schema_text())