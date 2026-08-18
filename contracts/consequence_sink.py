# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class ConsequenceRecord:
    attempts: u256
    applied: bool
    payload: str
    first_sender: Address


class ConsequenceSink(gl.Contract):
    """Idempotent child used by EXP-003.

    Every delivery attempt is counted, but the consequence is applied only once per
    case id. This lets the experiment measure duplicate child executions without
    turning duplicates into repeated irreversible effects.
    """

    records: TreeMap[str, ConsequenceRecord]
    total_attempts: u256
    unique_applied: u256

    def __init__(self):
        self.total_attempts = 0
        self.unique_applied = 0

    @gl.public.write
    def record_consequence(self, case_id: str, payload: str) -> None:
        if not case_id:
            raise gl.vm.UserError("case id is required")

        self.total_attempts += 1

        if case_id in self.records:
            record = self.records[case_id]
            record.attempts += 1
            return

        self.records[case_id] = ConsequenceRecord(
            attempts=1,
            applied=True,
            payload=payload,
            first_sender=gl.message.sender_address,
        )
        self.unique_applied += 1

    @gl.public.view
    def get_record(self, case_id: str) -> dict:
        if case_id not in self.records:
            return {
                "exists": False,
                "attempts": 0,
                "duplicate_count": 0,
                "applied": False,
                "payload": "",
                "first_sender": "",
            }

        record = self.records[case_id]
        attempts = int(record.attempts)
        return {
            "exists": True,
            "attempts": record.attempts,
            "duplicate_count": attempts - 1,
            "applied": record.applied,
            "payload": record.payload,
            "first_sender": record.first_sender.as_hex,
        }

    @gl.public.view
    def get_totals(self) -> dict:
        attempts = int(self.total_attempts)
        applied = int(self.unique_applied)
        return {
            "total_attempts": self.total_attempts,
            "unique_applied": self.unique_applied,
            "duplicate_attempts": attempts - applied,
        }
