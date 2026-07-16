"""Admin base — owner checks, audit logging, user resolving."""

import logging

from bot.core.services.auth import is_owner
from bot.core.services.auth import resolve_user_id as _resolve
from bot.database.database import get_connection

logger = logging.getLogger(__name__)


def resolve_user_id(user_input: str) -> str | None:
    return _resolve(user_input)


def is_owner_check(user_id: int, owner_id: int) -> bool:
    return is_owner(user_id, owner_id)


async def log_audit(
    action: str, target_user_id: str, target_username: str, moderator_id: str, db_path: str
):
    try:
        conn = get_connection(db_path)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO audit_logs (action, target_user_id, target_username, moderator_id)
               VALUES (?, ?, ?, ?)""",
            (action, target_user_id, target_username, moderator_id),
        )
        conn.commit()
        logger.info(
            "Audit: %s | target=%s (%s) | moderator=%s",
            action,
            target_username,
            target_user_id,
            moderator_id,
        )
    except Exception as e:
        logger.error("Failed to write audit log: %s", e)


def check_owner_send(ctx, bot) -> bool:
    return ctx.author.id == bot.config.owner_id
