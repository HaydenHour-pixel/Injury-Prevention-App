"""Enumerated values.

These exist for use in Python: the seed script, future Pydantic schemas, and the
scoring modules all reference the members rather than typing bare strings. The
database columns that hold them are plain `String`. There is no native enum type
and no CHECK constraint, so adding a member later is not a migration.

Every member's `.value` is exactly what is stored.
"""

from __future__ import annotations

from enum import StrEnum


class TrainingPhase(StrEnum):
    BASE = "base"
    BUILD = "build"
    PEAK = "peak"
    TAPER = "taper"
    RECOVERY = "recovery"
    OFF = "off"


class DataSource(StrEnum):
    """Maps to the source-confidence table in spec.md section 3."""

    STRAVA = "strava"
    MANUAL = "manual"
    UMASS_DINING_MENU = "umass_dining_menu"
    MANUAL_FOOD_ENTRY = "manual_food_entry"


class RecoveryMethodType(StrEnum):
    """`NONE` is a real, meaningful value: the athlete opened the recovery section
    and recorded that they did nothing. That is different from never opening it,
    which is the absence of a `recovery_method` row entirely (spec.md section 4).
    """

    NONE = "none"
    FOAM_ROLL = "foam_roll"
    YOGA = "yoga"
    ICE_BATH = "ice_bath"
    MASSAGE = "massage"
    STRETCHING = "stretching"
    REST = "rest"


class PainType(StrEnum):
    """Type and intensity are independent. A 7/10 muscle soreness and a 7/10 sharp
    pain are different events (spec.md section 5.5).
    """

    NONE = "none"
    MUSCLE_SORENESS = "muscle_soreness"
    DULL_ACHE = "dull_ache"
    SHARP_PAIN = "sharp_pain"


class PainOnset(StrEnum):
    SUDDEN = "sudden"
    GRADUAL = "gradual"
    UNKNOWN = "unknown"


class RecurrenceRisk(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class AlertLevel(StrEnum):
    """spec.md section 9. Level 1 logs only, level 2 is dashboard-only, level 3 pushes."""

    SILENT = "silent"
    SOFT = "soft"
    HARD = "hard"


class Outcome(StrEnum):
    """Calibration outcome captured every two weeks (spec.md section 10)."""

    NONE = "none"
    MILD_SORENESS = "mild_soreness"
    MODERATE_PAIN = "moderate_pain"
    SIGNIFICANT_PAIN = "significant_pain"
    CLINICAL_INJURY = "clinical_injury"


class CommitmentType(StrEnum):
    CLASS = "class"
    WORK = "work"
    OTHER = "other"


class StressEventType(StrEnum):
    EXAM = "exam"
    TRAVEL = "travel"
    ILLNESS = "illness"
    PERSONAL = "personal"
    WORK = "work"
    OTHER = "other"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
