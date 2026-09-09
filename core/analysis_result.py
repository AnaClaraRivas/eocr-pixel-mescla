from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.evidence import Evidence


@dataclass
class AnalysisResult:

    success: bool

    module: str

    score: int = 0

    data: Any = field(default_factory=dict)

    warnings: list[str] = field(default_factory=list)

    evidences: list[Evidence] = field(default_factory=list)

    execution_time: float = 0.0
