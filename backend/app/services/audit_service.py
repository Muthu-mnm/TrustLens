import hashlib
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import AuditEntry


def create_audit_entry(
    db: Session,
    application_id: str,
    action: str,
    actor: str,
    details: str
) -> AuditEntry:
    """
    Create and persist a tamper-evident audit log entry.
    Links the new entry to the previous entry hash to form a simplified audit chain.
    
    Note on design:
    This is an in-database cryptographic hash chain designed for verification of
    sequential integrity, not a distributed consensus blockchain.
    """
    # Fetch latest entry to chain hashes
    last_entry = (
        db.query(AuditEntry)
        .filter(AuditEntry.application_id == application_id)
        .order_by(AuditEntry.created_at.desc(), AuditEntry.id.desc())
        .first()
    )

    previous_hash = last_entry.entry_hash if last_entry and last_entry.entry_hash else "0" * 64
    timestamp = datetime.utcnow()

    # Compute entry hash: SHA256(application_id + action + actor + details + timestamp + previous_hash)
    payload = f"{application_id}:{action}:{actor}:{details}:{timestamp.isoformat()}:{previous_hash}"
    entry_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    entry = AuditEntry(
        id=str(uuid.uuid4()),
        application_id=application_id,
        action=action,
        actor=actor,
        details=details,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
        timestamp=timestamp,
        created_at=timestamp
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def verify_audit_chain(db: Session, application_id: str) -> dict:
    """
    Verify the cryptographic hash-chain integrity of audit log entries for an application.

    Verification guarantees:
    - Verifies sequential block linkages from genesis ("0"*64) to the latest entry.
    - An in-database hash chain is tamper-evident under the assumption of uncompromised
      database logs; it does not by itself prevent a privileged database administrator
      from modifying historical rows and recalculating subsequent hashes.
    - True immutability requires external write-once-read-many (WORM) storage or
      an independent public ledger notary service.

    Returns:
        dict: {
            "valid": bool,
            "total_entries": int,
            "broken_at_index": Optional[int],
            "details": str
        }
    """
    entries = (
        db.query(AuditEntry)
        .filter(AuditEntry.application_id == application_id)
        .order_by(AuditEntry.created_at.asc(), AuditEntry.id.asc())
        .all()
    )

    total = len(entries)
    if total == 0:
        return {
            "valid": True,
            "chain_valid": True,
            "total_entries": 0,
            "verified_entries": 0,
            "broken_at_index": None,
            "tampered_at_index": None,
            "details": "No audit entries exist for this application.",
            "message": "No audit entries exist for this application."
        }

    expected_prev = "0" * 64
    for idx, entry in enumerate(entries):
        # 1. Verify previous_hash linkage
        if (entry.previous_hash or "0" * 64) != expected_prev:
            err_msg = (
                f"Chain break at entry #{idx} (action: {entry.action}): "
                f"previous_hash '{entry.previous_hash}' does not match expected '{expected_prev}'."
            )
            return {
                "valid": False,
                "chain_valid": False,
                "total_entries": total,
                "verified_entries": idx,
                "broken_at_index": idx,
                "tampered_at_index": idx,
                "details": err_msg,
                "message": err_msg
            }

        # 2. Recompute current hash
        ts_str = entry.timestamp.isoformat() if entry.timestamp else entry.created_at.isoformat()
        payload = f"{entry.application_id}:{entry.action}:{entry.actor}:{entry.details}:{ts_str}:{entry.previous_hash}"
        recalculated_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        if entry.entry_hash != recalculated_hash:
            err_msg = (
                f"Content integrity failure at entry #{idx} (action: {entry.action}): "
                f"stored entry_hash '{entry.entry_hash}' does not match recalculated hash '{recalculated_hash}'."
            )
            return {
                "valid": False,
                "chain_valid": False,
                "total_entries": total,
                "verified_entries": idx,
                "broken_at_index": idx,
                "tampered_at_index": idx,
                "details": err_msg,
                "message": err_msg
            }

        expected_prev = entry.entry_hash

    success_msg = f"All {total} audit entries successfully verified with valid cryptographic hash chaining."
    return {
        "valid": True,
        "chain_valid": True,
        "total_entries": total,
        "verified_entries": total,
        "broken_at_index": None,
        "tampered_at_index": None,
        "details": success_msg,
        "message": success_msg
    }
