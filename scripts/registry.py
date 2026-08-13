from __future__ import annotations

import os
import subprocess


def login_ghcr() -> None:
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set")

    username = os.environ.get("GITHUB_ACTOR")

    if not username:
        raise RuntimeError("GITHUB_ACTOR is not set")

    process = subprocess.Popen(
        [
            "docker",
            "login",
            "ghcr.io",
            "-u",
            username,
            "--password-stdin",
        ],
        stdin=subprocess.PIPE,
        text=True,
    )

    process.communicate(token)

    if process.returncode != 0:
        raise RuntimeError("Failed to login to GHCR")
