from enum import StrEnum


class DatabaseRedistributionType2Type1(StrEnum):
    EVALUATION = "evaluation"
    INTERNAL = "internal"
    REDISTRIBUTE = "redistribute"

    def __str__(self) -> str:
        return str(self.value)
