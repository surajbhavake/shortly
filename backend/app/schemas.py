from datetime import datetime
from pydantic import BaseModel,Field,HttpUrl

class LinkCreate(BaseModel):
    url:HttpUrl
    custom_slug:str | None = Field(
        default=None,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0,9_-]+$",
    )

class LinkOut(BaseModel):
    slug:str
    url:str
    short_url:str
    clicks:int
    created_at:datetime | None=None

class LinkStats(BaseModel):
    slug: str
    url: str
    clicks: int