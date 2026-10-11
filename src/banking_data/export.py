import hashlib
import json
from pathlib import Path

import pandas as pd

NAMES = (
    "customers",
    "relationship_managers",
    "deposits",
    "loans",
    "credit_cards",
    "profitability",
    "products",
)


def write_outputs(tables, config, report, scenarios, output, reports):
    output, reports = Path(output), Path(reports)
    output.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in NAMES:
        frame = tables[name]
        keys = (
            ["customer_id", "month"]
            if "month" in frame
            else ["customer_id"]
            if "customer_id" in frame
            else ["rm_id"]
        )
        path = output / f"{name}.csv"
        frame.sort_values(keys).to_csv(
            path, index=False, float_format="%.6f", lineterminator="\n"
        )
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "generator_version": "0.1.0",
        "seed": config.seed,
        "customers": config.customers,
        "history_start": config.start,
        "history_end": config.end,
        "data_sources": [],
        "synthetic_only": True,
        "currency": "USD",
        "sha256": hashes,
        "simulation_scenarios": scenarios,
    }
    for name, value in [
        ("generation_manifest", manifest),
        ("validation_report", report),
    ]:
        (reports / f"{name}.json").write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def read_outputs(output):
    return {name: pd.read_csv(Path(output) / f"{name}.csv") for name in NAMES}
