from typing import Optional

from pydantic import BaseModel

class MessageSchema(BaseModel):
    id_wpp: str
    text: str

class MessageOut(BaseModel):
    response: str
    image_url: Optional[str] = None
