from dataclasses import dataclass


@dataclass(slots=True)
class Account:
    id: int
    email: str
    password: str
    active: bool
