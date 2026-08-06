from database.session import engine
from database.session import Base
from pathlib import Path

import database.models


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)