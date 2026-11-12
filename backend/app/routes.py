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


@router.get("/links",response_model=list[LinkOut])
async def list_links(db:AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Link)
        .order_by(
            Link.created_at.desc()
        )
    )

    links = result.scalars().all()

    pipe = redis.pipeline()
    for link in links:
        pipe.get(f"clicks:{link.slug}")
    counts = await pipe.execute()

    response = []

    for i , link in enumerate(links):

        item = LinkOut(
            slug = link.slug,
            url = link.url,
            short_url=f"{settings.base_url}/{link.slug}",
            clicks=int(counts[i] or 0),
            created_at = link.created_at,
        )

        response.append(item)

    return response



@router.get("/links/{slug}/stats",response_model=LinkStats)
async def get_stats(slug:str,db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(Link).where(Link.slug==slug))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404,"Link not found")

    clicks = await redis.get(f"clicks:{slug}")
    return LinkStats(slug=slug,url=link.url,clicks=int(clicks or 0))


@router.get("/{slug}")
async def redirect(slug:str,db:AsyncSession = Depends(get_db)):

    cached = await redis.get(f"link:{slug}")
    if cached:
        await redis.incr(f"clicks:{slug}")
        return RedirectResponse(cached,status_code=302)

    result = await db.execute(select(Link).where(Link.slug == slug))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404,"Link not found")

    await redis.set(f"link:{slug}",link.url,ex=settings.link_ttl_seconds)

    await redis.incr(f"clicks:{slug}")
    return RedirectResponse(link.url,status_code=302)