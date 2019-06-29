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

from typing import Dict, Optional

from aiohttp import web
from iomirea_rpc import Client, Server, Request
from iomirea_rpc.server import NoValue

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


async def restart_updater(
        srv: Server, req: Request,
        node: Optional[str] = None
    ) -> None:
    if node == srv.node:
        return NoValue

    clean_exit()


async def pull_all(srv: Server, req: Request) -> Dict[str, bool]:
    return {
        "code": pull("/code"),
        "api": pull("/api")
    }


async def pull_updater(srv: Server, req: Request) -> bool:
    return pull("/code")


async def pull_api(srv: Server, req: Request) -> bool:
    return pull("/api")


async def eval_updater(srv: Server, req: Request, code: str) -> str:
    return "Eval is not implemented yet"


async def init_rpc(app: web.Application) -> None:
    config = copy(app["config"]["redis"])
    host = config.pop("host")
    port = config.pop("port")

    app["api_rpc_client"] = Client("api", loop=app.loop)
    app["rpc_client"] = Client("updater", loop=app.loop)
    app["rpc_server"] = Server("updater", loop=app.loop)

    app.loop.create_task(app["api_rpc_client"].run((host, port), **config))
    app.loop.create_task(app["rpc_client"].run((host, port), **config))
    app.loop.create_task(app["rpc_server"].run((host, port), **config))

    app["rpc_server"].register_command(
        RPC_COMMAND_RESTART_UPDATER, restart_updater
    )
    app["rpc_server"].register_command(RPC_COMMAND_PULL_ALL, pull_all)
    app["rpc_server"].register_command(RPC_COMMAND_PULL_UPDATER, pull_updater)
    app["rpc_server"].register_command(RPC_COMMAND_PULL_API, pull_api)
    app["rpc_server"].register_command(RPC_COMMAND_EVAL_UPDATER, eval_updater)


async def stop_rpc(app: web.Application) -> None:
    app["api_rpc_client"].close()
    app["rpc_server"].close()
