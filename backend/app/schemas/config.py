from pydantic import BaseModel, field_validator


class ThresholdsOut(BaseModel):
    thresholds_days: list[int]


class ThresholdsUpdate(BaseModel):
    thresholds_days: list[int]

    @field_validator("thresholds_days")
    @classmethod
    def validate_thresholds(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("thresholds_days cannot be empty")
        if any(t < 0 for t in v):
            raise ValueError("thresholds cannot be negative — overdue is handled separately")
        # de-dupe and sort descending (30, 14, 7, 3, 1, 0) for predictable display
        return sorted(set(v), reverse=True)
