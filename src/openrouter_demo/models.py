from dataclasses import dataclass


@dataclass(frozen=True)
class Unavailable:
    label: str = "unavailable"

    def __bool__(self) -> bool:
        return False


UNAVAILABLE = Unavailable()
