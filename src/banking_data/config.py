from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    customers: int = 1000
    seed: int = 42
    start: str = "2024-01-01"
    end: str = "2025-12-01"
    rm_count: int = 20

    def __post_init__(self):
        if self.customers < 1:
            raise ValueError("Customer count must be positive")
