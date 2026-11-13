from contextlib import asynccontextmanager
from fastapi import FastAPI

from .database import Base,engine,redis_client as redis
from .routes import router

#manages applicatoin startup and shutdown
@asynccontextmanager
async def lifespan(app:FastAPI):
    #startup
    #create database table if they don't exist

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) #here conn is async but base.meta is sync
        #so we use run_sync it adapts the sync metadata operation to work with conn


        #check whether Redis is reachable

    await redis.ping()

    yield #here we pause the this lifespan function and start
        #accepting request here

    await redis.aclose() #close redis resources

    await engine.dispose()


app = FastAPI(
        title="Shortly",
        description="URL shortener with analytics",
        version="0.1.0",
        lifespan=lifespan
)

app.include_router(router)


