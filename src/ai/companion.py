# Companion — orchestrates the AI layer.
# Uses OpenAI when configured, otherwise a deterministic template engine so the
# demo never fails. All public methods return parsed dicts (never raw strings).
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from src.ai.memory import MemoryStore
from src.ai.prompts import (
    PLAN_SYSTEM,
    PLAN_USER_TEMPLATE,
    RECALL_SYSTEM,
    RECALL_USER_TEMPLATE,
    SUMMARY_SYSTEM,
    SUMMARY_USER_TEMPLATE,
)
from src.config import get_settings

logger = logging.getLogger(__name__)


def _safe_json(text: str) -> Dict[str, Any]:
    """Parse JSON from an LLM response, tolerating stray code fences."""
    cleaned = text.strip()
    cleaned = re.sub(r"^