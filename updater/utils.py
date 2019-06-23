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

import os
import signal

from git import Repo


def pull(path: str) -> None:
    repo = Repo(path)

    print(f"GIT: Pulling {path} <- {repo.remotes.origin.url}")

    repo.remotes.origin.pull()


def clean_exit() -> None:
    # avoid traceback
    os.kill(os.getpid(), signal.SIGINT)
