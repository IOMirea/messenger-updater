"""
IOMirea-updater - An updater for IOMirea messenger
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

import sys

from copy import copy

import aioredis

from aiohttp import web


async def reader(app, channel):
    while (await channel.wait_message()):
        msg = await channel.get_json()

        # a: action
        # d: data
        # t: send ts
        action = msg["a"]

        print(f"RPC: received {action}")
        if action == "restart":
            print("RPC: restarting")

            # TODO: figure out how to exit gracefully, without ugly traceback
            sys.exit(0)
        else:
            print("RPC: unknown action")


async def init_rpc(app: web.Application) -> None:
    config = copy(app["config"]["redis"])
    host = config.pop("host")
    port = config.pop("port")

    app["pub"] = await aioredis.create_redis((host, port), **config)
    app["sub"] = await aioredis.create_redis((host, port), **config)

    channels = await app["sub"].subscribe("rpc:updater")
    app.loop.create_task(reader(app, channels[0]))


async def stop_rpc(app: web.Application) -> None:
    app["pub"].close()
    app["sub"].close()
