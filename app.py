"""
IOMirea-server - An updater for IOMirea messenger
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
import argparse

from pathlib import Path

import yaml
import docker

from aiohttp import web

argparser = argparse.ArgumentParser(description="IOMirea server updater")
argparser.add_argument(
    "--config-file",
    type=Path,
    default=Path("/config/config.yaml"),
    help="Path to the data directory",
)


async def github_webhook(req: web.Request) -> web.Response:
    header_signature = req.headers.get("X-Hub-Signature")
    if not header_signature:
        raise web.HTTPUnauthorized(reason="Missing signature header")

    secret = req.app["config"]["github-webhook-token"]

    sha_name, delim, signature = header_signature.partition("=")
    if not (sha_name or delim or signature):
        raise web.HTTPUnauthorized(reason="Bad signature header")

    mac = hmac.new(secret.encode(), msg=await req.read(), digestmod="sha1")

    if not hmac.compare_digest(mac.hexdigest(), signature):
        raise web.HTTPUnauthorized

    # TODO:
    # - git pull
    # - git pull workers
    # - stop workers
    # - perform config migration
    # - perform database migration
    # - restart (if needed)
    # - docker pull workers if needed
    # - start workers

    return web.Response()


if __name__ == "__main__":
    app = web.Application()

    app["args"] = argparser.parse_args()

    with open(app["args"].config_file, "r") as f:
        app["config"] = yaml.load(f, Loader=yaml.SafeLoader)

    app["docker"] = docker.from_env()

    app.add_routes([web.get("/github-webhook", github_webhook)])

    web.run_app(
        app,
        port=app["config"]["updater"]["port"],
        host=app["config"]["updater"]["host"],
    )