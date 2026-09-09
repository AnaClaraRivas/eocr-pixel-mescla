from dataclasses import dataclass


@dataclass
class Evidence:

    code: str
    message: str
    severity: str
    weight: int
