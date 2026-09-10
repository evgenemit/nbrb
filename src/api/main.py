import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from redis_fastapi import FastAPIRedis, redis_lifespan

from api.endpoints import router as main_router
from background_tasks.nbrb_parser import add_byn, update_currencies

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with redis_lifespan(app):
        scheduler = AsyncIOScheduler()
        scheduler.add_job(update_currencies, 'interval', days=1, args=[0])
        scheduler.add_job(update_currencies, 'interval', days=1, args=[1])
        scheduler.start()

        task1 = asyncio.create_task(update_currencies(0))
        task2 = asyncio.create_task(update_currencies(1))
        await task1
        await task2
        await add_byn()

        yield
        scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
FastAPIRedis(app).caching()
app.include_router(main_router)
