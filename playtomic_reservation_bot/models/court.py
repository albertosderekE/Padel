from dataclasses import dataclass


@dataclass(slots=True)
class Court:
    id: int
    club_id: int
    name: str
    booking_fragment_url: str
