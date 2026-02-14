from dataclasses import dataclass


@dataclass(slots=True)
class Club:
    id: int
    name: str
    base_url: str
