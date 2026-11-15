import logging
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from api.models.models import AuditLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AppLogger")

class DbLogger:
    @staticmethod
    def log_event(
        db: Session, 
        level: str, 
        event_type: str, 
        message: str, 
        user_id: int = None, 
        meta: dict = None
    ):

        try:
            console_msg = f"[{level}] {event_type}: {message}"
            if level == "ERROR":
                logger.error(console_msg)
            else:
                logger.info(console_msg)

            audit = AuditLog(
                user_id=user_id,
                level=level,
                event_type=event_type,
                message=message,
                metadata_info=meta if meta else {},
                created_at=datetime.now(timezone.utc)
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            logger.error(f"FALHA AO GRAVAR LOG DE AUDITORIA: {str(e)}")
            db.rollback()