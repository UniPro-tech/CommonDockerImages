from __future__ import annotations

import re

import requests


SESSION = requests.Session()

SESSION.headers.update(
    {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CommonDockerImages/1.0",
    }
)


def get_latest_release_tag(
    repository: str,
    pattern: str,
) -> str | None:
    """
    GitHub Releasesから最新版を取得する。
    """

    url = f"https://api.github.com/repos/{repository}/releases"

    response = SESSION.get(
        url,
        params={
            "per_page": 100,
        },
        timeout=30,
    )

    response.raise_for_status()

    releases = response.json()

    regex = re.compile(pattern)

    versions = []

    for release in releases:
        if release.get("draft"):
            continue

        if release.get("prerelease"):
            continue

        tag = release.get("tag_name")

        if not tag:
            continue

        tag = tag.lstrip("v")

        if regex.fullmatch(tag):
            versions.append(tag)

    if not versions:
        return None

    return max(
        versions,
        key=_version_key,
    )


def _version_key(value: str):
    return tuple(int(x) for x in value.split("."))
