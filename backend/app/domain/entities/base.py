"""
CogniFy Entity Base
Mixin for automatic serialization of dataclass entities
"""

import dataclasses
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Set
from uuid import UUID


class SerializableMixin:
    """
    Mixin that auto-generates `to_dict()` for dataclass entities.

    Conversion rules:
      - UUID   → str
      - Enum   → .value
      - datetime → .isoformat()
      - List/Dict → recursively converted
      - None values are preserved as None

    Subclasses can set `_exclude_fields` to skip specific fields:
        _exclude_fields: ClassVar[Set[str]] = {"password_hash", "embedding"}
    """

    _exclude_fields: ClassVar[Set[str]] = set()

    def to_dict(self) -> dict:
        """Auto-serialize all dataclass fields to a JSON-safe dict"""
        result = {}
        for f in dataclasses.fields(self):  # type: ignore[arg-type]
            if f.name in self._exclude_fields:
                continue
            value = getattr(self, f.name)
            result[f.name] = self._convert_value(value)
        return result

    @staticmethod
    def _convert_value(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, list):
            return [SerializableMixin._convert_value(v) for v in value]
        if isinstance(value, dict):
            return {k: SerializableMixin._convert_value(v) for k, v in value.items()}
        if dataclasses.is_dataclass(value) and hasattr(value, "to_dict"):
            return value.to_dict()
        return value
