"""
Константы приложения.
Слой: конфигурация.
"""

from enum import StrEnum


class Status(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
