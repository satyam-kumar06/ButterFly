"""Export deterministic schemas, or fail if committed schemas have drifted."""

import argparse
import json
from pathlib import Path

from apps.api.contracts import (
    Branch,
    ContractBundle,
    DecisionSpec,
    DistributionSchema,
    Results,
    StreamEventSchema,
    VariableSchema,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    models = {
        "contracts": ContractBundle,
        "decision-spec": DecisionSpec,
        "results": Results,
        "branch": Branch,
        "stream-event": StreamEventSchema,
        "distribution": DistributionSchema,
        "variable": VariableSchema,
    }
    for name, model in models.items():
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        path = ROOT / "docs" / "schemas" / f"{name}.schema.json"
        content = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale schema: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print(f"{'Checked' if args.check else 'Exported'} {len(models)} schemas")


if __name__ == "__main__":
    main()
