"""Process-wide configuration. Single athlete, single deployment: env vars,
not a settings table.
"""

from __future__ import annotations

import os

# spec.md section 2 defines `date` as the athlete's local calendar date, and
# app/provenance.py needs a timezone to convert a UTC `created_at` into that
# local calendar date for the recall-decay math. There is no timezone field on
# athlete_profile (spec.md doesn't define one, and adding one wasn't asked for
# in this slice), so this is a deployment-wide assumption rather than
# per-athlete data. Hayden is on the US east coast for the MVP validation
# window; override via env var if that's wrong.
ATHLETE_TIMEZONE = os.environ.get("ATHLETE_TIMEZONE", "America/New_York")

# CORS: an explicit allow-list, not a wildcard — the frontend's dev origin by
# default, plus whatever the deployed origin turns out to be once this is on
# Fly.io. Comma-separated, so a deployment sets one env var rather than
# needing a code change.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
