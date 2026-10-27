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
        .order_by(AuditEntry.created_at.desc())
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
