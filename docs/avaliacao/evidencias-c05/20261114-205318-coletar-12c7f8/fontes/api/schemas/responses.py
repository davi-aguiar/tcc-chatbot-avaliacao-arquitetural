from typing import Optional

from pydantic import BaseModel


class ChatResponse(BaseModel):
    text: str
    image_url: Optional[str] = None
