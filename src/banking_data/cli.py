import argparse
import json
from pathlib import Path

import numpy as np

from .config import Config
from .customers import create_profiles
from .export import read_outputs, write_outputs
from .financials import simulate
from .validation import validate


def generate(config):
    rng = np.random.default_rng(config.seed)
    customers, rms = create_profiles(config, rng)
    monthly, scenarios = simulate(customers, config, rng)
    return {"customers": customers, "relationship_managers": rms, **monthly}, scenarios


def main():
    parser = argparse.ArgumentParser(
        description="Entirely fictional banking data, Jan 2024–Dec 2025."
    )
    parser.add_argument("action", choices=["generate", "validate"])
    parser.add_argument("--customers", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()
    config = Config(customers=args.customers, seed=args.seed)
    if args.action == "generate":
        tables, scenarios = generate(config)
        report = validate(tables, config)
        write_outputs(tables, config, report, scenarios, args.output, args.reports)
        # Validate actual serialized values as well.
        validate(read_outputs(args.output), config)
    else:
        report = validate(read_outputs(args.output), config)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
