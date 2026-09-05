from enum import StrEnum


class DatabaseChecksumV2Response200Format(StrEnum):
    CSVGZ = "csvgz"
    MMDB = "mmdb"

    def __str__(self) -> str:
        return str(self.value)
