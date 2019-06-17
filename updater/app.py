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

import yaml

from aiohttp import web

from cli import args
from migrate import migrate


async def on_startup(app: web.Application) -> None:
    await migrate(app)


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


async def updater_wh(req: web.Request) -> web.Response:
    await verify_github_request(req)

    # TODO:
    # - git pull
    # - git pull workers
    # - stop workers
    # - perform config migration (parallel?)
    # - perform database migration (parallel?)
    # - restart (if needed)
    # - start workers

    return web.Response()


async def api_wh(req: web.Request) -> web.Response:
    await verify_github_request(req)

    # TODO: everything

    return web.Response()


if __name__ == "__main__":
    app = web.Application()

    with open(args.config_file, "r") as f:
        app["config"] = yaml.load(f, Loader=yaml.SafeLoader)

    app["args"] = args

    app.on_startup.append(on_startup)

    app.add_routes([web.post("/wh/github/updater", updater_wh)])
    app.add_routes([web.post("/wh/github/api", api_wh)])

    web.run_app(
        app,
        host=app["args"].host,
        port=app["args"].port,
    )
