"""Import every model module so `Base.metadata` is complete.

Alembic's `--autogenerate` and the tests' `Base.metadata.create_all()` both walk
`Base.metadata`, which only knows about a table once its module has been
imported somewhere. Importing this package is how that happens.
"""

from app.models.athlete import Athlete, AthleteProfile
from app.models.base import Base
from app.models.context import LifestyleCommitment, StressEvent
from app.models.daily import DailyEntry, Nutrition, RecoveryMethod, Sleep, Training
from app.models.model_meta import ModelMetrics, PredictionAccuracy
from app.models.symptoms import BodyPartVulnerability, PainProfile, Symptom

__all__ = [
    "Base",
    "Athlete",
    "AthleteProfile",
    "DailyEntry",
    "Training",
    "Sleep",
    "Nutrition",
    "RecoveryMethod",
    "Symptom",
    "PainProfile",
    "BodyPartVulnerability",
    "LifestyleCommitment",
    "StressEvent",
    "PredictionAccuracy",
    "ModelMetrics",
]
