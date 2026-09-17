# ==========================================================
# Melanated AZ - Social links -> community member profile sync
# ==========================================================

import json
import logging
import os
import sqlite3

CHAT_ID = -1002697105809
COMMUNITY_DB = os.environ.get("COMMUNITY_DB", "/var/data/community_security.db").strip()
SOCIAL_DB = os.environ.get("SOCIAL_MEDIA_DB", "/var/data/social_media.db").strip()

logger = logging.getLogger(__name__)


def _connect(path):
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def sync_social_profiles():
    """Copy current social links into the saved community member profile record.

    The social_media database remains the source of truth for links. The
    community member bank also receives a JSON snapshot so the saved member
    profile contains the social information without changing existing member
    data or introductions.
    """
    if not os.path.exists(COMMUNITY_DB) or not os.path.exists(SOCIAL_DB):
        return

    social = _connect(SOCIAL_DB)
    community = _connect(COMMUNITY_DB)
    try:
        columns = {r["name"] for r in community.execute("PRAGMA table_info(community_members)").fetchall()}
        if "social_links" not in columns:
            community.execute("ALTER TABLE community_members ADD COLUMN social_links TEXT")
        if "social_links_updated_at" not in columns:
            community.execute("ALTER TABLE community_members ADD COLUMN social_links_updated_at TEXT")

        rows = social.execute(
            "SELECT user_id, platform, url, display_name, username, updated_at "
            "FROM social_links ORDER BY user_id, platform"
        ).fetchall()

        grouped = {}
        for row in rows:
            grouped.setdefault(int(row["user_id"]), []).append({
                "platform": row["platform"],
                "url": row["url"],
                "display_name": row["display_name"],
                "username": row["username"],
                "updated_at": row["updated_at"],
            })

        for user_id, links in grouped.items():
            latest = max((x.get("updated_at") or "" for x in links), default=None)
            community.execute(
                "UPDATE community_members SET social_links=?, social_links_updated_at=? "
                "WHERE chat_id=? AND user_id=?",
                (json.dumps(links, ensure_ascii=False), latest, CHAT_ID, user_id),
            )

        community.commit()
        logger.info("Social member profile sync complete | profiles=%s", len(grouped))
    except Exception:
        community.rollback()
        logger.exception("Social member profile sync failed")
    finally:
        social.close()
        community.close()
