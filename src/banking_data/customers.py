import numpy as np
import pandas as pd
from faker import Faker

INDUSTRIES = {
    "Retail": (0.10, 0.18, 11),
    "Construction": (0.13, 0.16, 6),
    "Professional Services": (0.23, 0.05, 8),
    "Manufacturing": (0.12, 0.08, 9),
    "Hospitality": (0.09, 0.20, 7),
    "Wholesale": (0.08, 0.10, 10),
}


def create_profiles(config, rng):
    fake = Faker("en_US")
    fake.seed_instance(config.seed)
    rms = pd.DataFrame(
        [
            {
                "rm_id": f"SYN-RM{i:03d}",
                "rm_name": f"Fictional RM {i:03d}",
                "region": f"Region {(i - 1) % 4 + 1}",
            }
            for i in range(1, config.rm_count + 1)
        ]
    )
    rows = []
    for i in range(1, config.customers + 1):
        industry = str(rng.choice(list(INDUSTRIES)))
        annual = round(float(np.clip(rng.lognormal(14.2, 0.95), 150000, 30000000)), 2)
        rm = rms.iloc[(i - 1) % config.rm_count]
        rows.append(
            {
                "customer_id": f"SYN-C{i:06d}",
                "business_name": f"Fictional {fake.word().title()} Business {i:04d}",
                "industry": industry,
                "business_size": "Small"
                if annual < 1000000
                else "Medium"
                if annual < 5000000
                else "Large",
                "business_age_years": int(rng.integers(2, 36)),
                "region": rm.region,
                "rm_id": rm.rm_id,
                "relationship_start_month": f"{int(rng.integers(2018, 2024))}-01-01",
                "baseline_annual_business_revenue": annual,
                "is_synthetic": True,
            }
        )
    return pd.DataFrame(rows), rms
