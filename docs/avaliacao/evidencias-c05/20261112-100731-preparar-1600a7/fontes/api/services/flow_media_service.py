from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from api.models.models import FlowMedia


class FlowMediaService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_image_url(self, flow_key: str, default: str = None) -> str:
        try:
            media = (
                self.db.query(FlowMedia)
                .filter(
                    FlowMedia.flow_key == flow_key.upper(),
                    FlowMedia.media_type == "image",
                    FlowMedia.is_active == True,
                )
                .order_by(FlowMedia.updated_at.desc(), FlowMedia.id.desc())
                .first()
            )
        except (ProgrammingError, OperationalError):
            self.db.rollback()
            return default

        if media:
            return media.media_url

        return default
