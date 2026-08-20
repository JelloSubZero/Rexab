import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

BASE_DIR = Path(__file__).resolve().parent.parent


def _upgrade_to_head():
    alembic_cfg = Config(str(BASE_DIR / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


async def init_db():
    # alembic's upgrade() runs its own asyncio.run() internally, which
    # can't be nested inside the bot's already-running event loop, so
    # it's dispatched to a worker thread instead.
    await asyncio.to_thread(_upgrade_to_head)
