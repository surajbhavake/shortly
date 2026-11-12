from datetime import datetime,timezone
from sqlalchemy import DateTime,String
from sqlalchemy.orm import Mapped,mapped_column

from .database import Base


class Link(Base):
    __tablename__ = "links"

    #basically it generate a id for the url
    slug:Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    url:Mapped[str] = mapped_column(
        String(2048),
        nullable=False
    )

    created_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda:datetime.now(timezone.utc),
        nullable=False,
    )

