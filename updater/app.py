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

import hmac
import asyncio

import yaml

from aiohttp import web

from cli import args
from rpc import (
        init_rpc, stop_rpc, RPC_COMMAND_RESTART_UPDATER, RPC_COMMAND_RESTART_API,
        RPC_COMMAND_PULL_UPDATER, RPC_COMMAND_PULL_API
    )
from migrate import migrate
from utils import pull, clean_exit


async def on_startup(app: web.Application) -> None:
    await migrate(app)
    await init_rpc(app)


async def on_cleanup(app: web.Application) -> None:
    await stop_rpc(app)


async def verify_github_request(req: web.Request) -> None:
    header_signature = req.headers.get("X-Hub-Signature")
    if not header_signature:
        raise web.HTTPUnauthorized(reason="Missing signature header")

    secret = req.app["config"]["github-webhook-token"]

    sha_name, delim, signature = header_signature.partition("=")
    if not (sha_name or delim or signature):
        raise web.HTTPUnauthorized(reason="Bad signature header")

    mac = hmac.new(secret.encode(), msg=await req.read(), digestmod="sha1")

    if not hmac.compare_digest(mac.hexdigest(), signature):
        raise web.HTTPUnauthorized(reason="Hashes did not match")


async def update_updaters() -> None:
    await app["rpc_client"].call(RPC_COMMAND_PULL_UPDATER, timeout=15)

    # TODO: only restart nodes with successfull pull

    await app["rpc_client"].call(
        RPC_COMMAND_RESTART_UPDATER, {"node": app["rpc_server"].node}
    )

    # update self
    clean_exit()


async def update_apis() -> None:
    await app["rpc_client"].call(RPC_COMMAND_PULL_API, timeout=15)

    # TODO: only restart nodes with successfull pull

    await app["api_rpc_client"].call(RPC_COMMAND_RESTART_API)


async def updater_wh(req: web.Request) -> web.Response:
    await verify_github_request(req)

    print("UPDATER webhook fired")

    asyncio.create_task(update_updaters())

    return web.Response()


async def api_wh(req: web.Request) -> web.Response:
    await verify_github_request(req)

    print("API webhook fired")

    asyncio.create_task(update_apis())

    return web.Response()


if __name__ == "__main__":
    pull("/code")

    app = web.Application()

    with open(args.config_file, "r") as f:
        app["config"] = yaml.load(f, Loader=yaml.SafeLoader)

    app["args"] = args

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    app.add_routes([web.post("/wh/github/updater", updater_wh)])
    app.add_routes([web.post("/wh/github/api", api_wh)])

    web.run_app(app, host=app["args"].host, port=app["args"].port)
