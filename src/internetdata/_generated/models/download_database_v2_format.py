from enum import StrEnum


class DownloadDatabaseV2Format(StrEnum):
    CSVGZ = "csvgz"
    MMDB = "mmdb"

    def __str__(self) -> str:
        return str(self.value)
