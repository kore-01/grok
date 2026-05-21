#!/usr/bin/env python3
"""Import SSO tokens from sso.txt into the local SQLite account database."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))

from app.control.account.backends.local import LocalAccountRepository
from app.control.account.commands import AccountUpsert
from app.platform.paths import data_path


async def import_tokens(txt_path: Path | None = None) -> int:
    """Read tokens from sso.txt and upsert into the account database."""
    txt_path = txt_path or _PROJECT_ROOT / "sso.txt"
    if not txt_path.exists():
        print(f"Error: {txt_path} not found")
        return 1

    raw_tokens: list[str] = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            token = line.strip()
            if token:
                raw_tokens.append(token)

    if not raw_tokens:
        print("Error: no tokens found in sso.txt")
        return 1

    db_path = data_path("accounts.db")
    repo = LocalAccountRepository(db_path)
    await repo.initialize()

    # Remove duplicates while preserving order
    seen: set[str] = set()
    upserts: list[AccountUpsert] = []
    for token in raw_tokens:
        if token not in seen:
            seen.add(token)
            upserts.append(AccountUpsert(token=token))

    result = await repo.upsert_accounts(upserts)
    await repo.close()

    print(f"Imported {result.upserted} accounts into {db_path}")
    if result.patched:
        print(f"  (updated {result.patched} existing)")
    return 0


if __name__ == "__main__":
    txt = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(asyncio.run(import_tokens(txt)))
