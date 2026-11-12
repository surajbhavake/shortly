from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db
from .database import redis_client as redis
from .models import Link
from .schemas import LinkCreate,LinkOut,LinkStats
from .shortener import generate_slug

router = APIRouter()

@router.get("/health")
async def health():
    return {"status":"ok"}

@router.post("/links",response_model=LinkOut,status_code=status.HTTP_201_CREATED)
async def create_link(payload:LinkCreate,db:AsyncSession = Depends(get_db)):
    url_str = str(payload.url)
    slug = payload.custom_slug

    if slug:
        if await redis.exists(f"link:{slug}"):
            raise HTTPException(status.HTTP_409_CONFLICT,"Slug already taken")

        existing = await db.execute(select(Link).where(Link.slug == slug))
        if existing.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT,"Slug already taken")

    else :

        for _ in range(10):
            slug = generate_slug()
            if not await redis.exists(f"link:{slug}"):
                break
        else:
            raise HTTPException(500,"Could not genslugerate unique slug")


    link = Link(slug=slug,url=url_str)
    db.add(link)
    await db.commit()
    await db.refresh(link)


    await redis.set(
        f"link:{slug}",
        url_str,
        ex=settings.link_ttl_seconds
    )

    return LinkOut(
        slug=slug,
        url = url_str,
        short_url = f"{settings.base_url}/{slug}",
        clicks = 0,
        created_at = link.created_at,
    )