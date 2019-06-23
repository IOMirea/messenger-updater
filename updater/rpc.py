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

from copy import copy
from typing import Dict, Any

import aioredis

from aiohttp import web

from utils import pull, clean_exit


RPC_COMMAND_RESTART_ALL = 100
RPC_COMMAND_RESTART_UPDATER = 101
RPC_COMMAND_RESTART_API = 102

RPC_COMMAND_PULL_ALL = 200
RPC_COMMAND_PULL_UPDATER = 201
RPC_COMMAND_PULL_API = 202

RPC_COMMAND_EVAL_ALL = 300
RPC_COMMAND_EVAL_UPDATER = 301
RPC_COMMAND_EVAL_API = 302

RPC_CHANNEL_UPDATER = "rpc:updater"
RPC_RESPONSE_CHANNEL = "rpc:updater-response"


async def reader(
    app: web.Application, channel: aioredis.pubsub.Channel
) -> None:
    print(f"RPC: listening {RPC_CHANNEL_UPDATER}")

    while await channel.wait_message():
        try:
            payload = await channel.get_json()
        except Exception as e:
            print(f"RPC: error decoding message: {e}")

        try:
            await process_command(app, payload)
        except Exception as e:
            print(
                f"RPC: error processing command: {e.__class__.__name__}: {e}; Payload: {payload}"
            )

    print(f"RPC: stopped listening {RPC_CHANNEL_UPDATER}")


async def send_response(
    app: web.Application, address: str, response: str
) -> None:
    # a: address
    # r: string response
    await app["pub"].publish_json(
        RPC_RESPONSE_CHANNEL, {"a": address, "r": response}
    )


async def process_command(
    app: web.Application, payload: Dict[str, Any]
) -> None:
    # c: command, int
    # a: address, string
    # d: data, json

    command = payload["c"]
    # address = payload["a"]
    # data = payload.get("d", {})

    print(f"RPC: received command {command}")

    if command == RPC_COMMAND_RESTART_UPDATER:
        print("RPC: restarting")

        clean_exit()

    elif command == RPC_COMMAND_PULL_ALL:
        pull("/code")
        pull("/api")

    elif command == RPC_COMMAND_PULL_UPDATER:
        pull("/code")

    elif command == RPC_COMMAND_PULL_API:
        pull("/api")

    elif command == RPC_COMMAND_EVAL_UPDATER:
        # TODO
        pass

    else:
        print("RPC: unknown command")


async def init_rpc(app: web.Application) -> None:
    config = copy(app["config"]["redis"])
    host = config.pop("host")
    port = config.pop("port")

    app["pub"] = await aioredis.create_redis((host, port), **config)
    app["sub"] = await aioredis.create_redis((host, port), **config)

    channels = await app["sub"].subscribe(RPC_CHANNEL_UPDATER)
    app.loop.create_task(reader(app, channels[0]))


async def stop_rpc(app: web.Application) -> None:
    app["pub"].close()
    app["sub"].close()
