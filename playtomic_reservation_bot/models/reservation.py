from dataclasses import dataclass


@dataclass(slots=True)
class Reservation:
    id: int
    court_id: int
    account_id: int
    play_datetime_local: str
    execution_datetime_local: str
    status: str
    created_at: str
