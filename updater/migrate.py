"""
IOMirea-server - A server for IOMirea messenger
Copyright (C) 2019  Eugene Ershov

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import time
import importlib

from typing import Dict, Any, Optional, List

import yaml
import asyncpg

from aiohttp import web

from migration import BaseMigration
from utils import init_logger, migrate_log


async def get_config_version(config: Dict[str, Any]) -> int:
    return config.get("config-version", -1)


async def get_pg_version(connection: asyncpg.Connection) -> int:
    try:
        record = await connection.fetchrow(
            "SELECT version FROM versions WHERE name='database';"
        )
        return record["version"]
    except asyncpg.exceptions.UndefinedTableError:
        return -1


def get_migrations(
    path: str,
    config: Dict[str, Any],
    connection: Optional[asyncpg.Connection] = None,
) -> List[BaseMigration]:
    """
    Returns a list of migration objects created from path variable.
    All migration files should match pattern: ^[a-Z]+.py$
    """

    migrations = []

    package_path_base = f'{".".join(path.split(os.path.sep)[1:])}.'
    for entry in os.listdir(path):
        if not entry.endswith(".py"):
            continue

        entry = entry[:-3]  # strip '.py'

        front, delim, rest = entry.partition("_")
        if not delim:
            continue

        try:
            version = int(front)
        except ValueError:
            continue

        migration_class = getattr(
            importlib.import_module(package_path_base + entry), "Migration"
        )

        if connection is None:  # config migration
            migrations.append(migration_class(version, config))
        else:
            migrations.append(migration_class(version, connection))

    return migrations


async def perform_config_migration(config: Dict[str, Any]) -> Dict[str, Any]:
    migrations = get_migrations("updater/migrations/config", config)
    current_version = await get_config_version(config)

    migrations = [m for m in migrations if m.version > current_version]

    if not migrations:
        return config

    migrations.sort(key=lambda m: m.version)
    latest = migrations[-1].version

    migrate_log(
        f'Beginning config migrations: {" -> ".join([str(current_version)] + [str(m.version) for m in migrations])}'
    )

    try:
        for m in migrations:
            migrate_log(f"Started  migration {m.version} ...")

            begin = time.time()
            config = await m._up(latest)
            end = time.time()

            migrate_log(
                f"Finished migration {m.version} in {round((end - begin) * 1000, 3)}ms"
            )
    except Exception as e:
        migrate_log(f"Exception: {e}")
        sys.exit(1)

    migrate_log(f"Successfully finished {len(migrations)} config migrations")

    return config


async def perform_pg_migration(
    config: Dict[str, Any], connection: asyncpg.Connection
) -> None:
    migrations = get_migrations(
        "updater/migrations/postgres", config, connection
    )
    current_version = await get_pg_version(connection)

    migrations = [m for m in migrations if m.version > current_version]

    if not migrations:
        return

    migrations.sort(key=lambda m: m.version)
    latest = migrations[-1].version

    if current_version == -1:  # database is not initialized, run migration 0
        migrations = [migrations[0]]

    migrate_log(
        f'Beginning database migrations: {" -> ".join([str(current_version)] + [str(m.version) for m in migrations])}'
    )

    try:
        for m in migrations:
            migrate_log(f"Started  migration {m.version} ...")

            begin = time.time()
            await m._up(latest)
            end = time.time()

            migrate_log(
                f"Finished migration {m.version} in {round((end - begin) * 1000, 3)}ms"
            )
    except Exception as e:
        migrate_log(f"Exception: {e}")
        sys.exit(1)
    finally:
        await connection.close()

    migrate_log(f"Successfully finished {len(migrations)} database migrations")


async def migrate(app: web.Application) -> None:
    init_logger(app["config"])
    new_config = await perform_config_migration(app["config"])
    init_logger(new_config)

    with open(app["args"].config_file, "w") as f:
        f.write(yaml.dump(new_config, default_flow_style=False))

    app["config"] = new_config

    pg_connection = await asyncpg.connect(**app["config"]["postgres"])

    if os.environ.get("LEADER", "0") == "0":
        migrate_log("Not leader, skipping postgres migration")
        return

    migrate_log("Leader, starting postgres migration")
    await perform_pg_migration(app["config"], pg_connection)
