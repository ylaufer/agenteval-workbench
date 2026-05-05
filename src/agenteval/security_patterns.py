"""Canonical security patterns shared between the dataset validator and SecurityEvaluator."""
from __future__ import annotations

import re

# Patterns that indicate definite secret leakage.
# Used by both the dataset validator (commit-time) and the SecurityEvaluator (scoring-time).
SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"sk-[A-Za-z0-9]{10,}"),
    re.compile(r"(?i)authorization:\s*bearer\s+[a-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)\bapi[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}['\"]?"),
    re.compile(r"(?i)\btoken\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}['\"]?"),
]

# Patterns indicating risky-but-not-definite leakage (used only by SecurityEvaluator).
RISKY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)password\s*[:=]\s*[^\s]+"),
    re.compile(r"(?i)secret\s*[:=]\s*[^\s]+"),
    re.compile(r"(?i)credential"),
]
