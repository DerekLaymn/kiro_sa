"""typediff - differential testing adjudicator for mypy vs ty (pyright as optional tie-breaker)."""

from .models import Dismissal, EvidenceType, Symptom, Tier, Verdict
from .pipeline import Pipeline, PipelineConfig

__all__ = ["Pipeline", "PipelineConfig", "Symptom", "Dismissal", "EvidenceType", "Verdict", "Tier"]
__version__ = "0.1.0"
