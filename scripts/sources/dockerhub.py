from __future__ import annotations

import re
from typing import Iterable

import requests


API_BASE = "https://hub.docker.com/v2/repositories"


SESSION = requests.Session()

SESSION.headers.update(
    {
        "Accept": "application/json",
        "User-Agent": "CommonDockerImages/1.0",
    }
)


def _request(
    url: str,
    params: dict | None = None,
) -> dict:
    response = SESSION.get(
        url,
        params=params,
        timeout=30,
    )

    if response.status_code == 403:
        raise RuntimeError(
            "Docker Hub API returned HTTP 403.\n"
            f"URL: {response.url}\n"
            "Docker Hub API access/rate-limit restriction "
            "may have been reached."
        )

    if response.status_code == 429:
        raise RuntimeError(
            "Docker Hub API returned HTTP 429.\n"
            f"URL: {response.url}\n"
            "Docker Hub API rate limit exceeded."
        )

    response.raise_for_status()

    return response.json()


def get_tags(
    repository: str,
    *,
    max_pages: int = 3,
) -> list[str]:
    """
    Docker Hubのタグを取得する。

    全ページを無制限に取得しない。
    """

    url = f"{API_BASE}/{repository}/tags/"

    params = {
        "page_size": 100,
    }

    tags: list[str] = []

    for _ in range(max_pages):
        data = _request(
            url,
            params=params,
        )

        for result in data.get("results", []):
            name = result.get("name")

            if name:
                tags.append(name)

        url = data.get("next")

        if not url:
            break

        params = None

    return tags


def get_latest_matching_tag(
    repository: str,
    pattern: str,
    *,
    minimum_major: int | None = None,
    max_pages: int = 3,
) -> str | None:
    """
    Docker Hubから指定patternに一致する最新版を取得する。
    """

    regex = re.compile(pattern)

    tags = get_tags(
        repository,
        max_pages=max_pages,
    )

    matched: list[str] = []

    for tag in tags:
        if not regex.fullmatch(tag):
            continue

        if minimum_major is not None:
            try:
                major = int(tag.split(".")[0])
            except (ValueError, IndexError):
                continue

            if major < minimum_major:
                continue

        matched.append(tag)

    if not matched:
        return None

    def version_key(value: str):
        parts = []

        for part in value.split("."):
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(0)

        return tuple(parts)

    return max(
        matched,
        key=version_key,
    )


def get_latest_major_versions(
    repository: str,
    majors: Iterable[int],
) -> dict[str, str]:
    """
    PostgreSQLなどのmajorごとの最新版を取得する。

    例えば:

        {
            "15": "15.14",
            "16": "16.10",
            "17": "17.6",
            "18": "18.4"
        }
    """

    tags = get_tags(
        repository,
        max_pages=5,
    )

    result: dict[str, str] = {}

    target_majors = {str(major) for major in majors}

    pattern = re.compile(r"^(\d+)\.(\d+)$")

    for tag in tags:
        match = pattern.fullmatch(tag)

        if not match:
            continue

        major = match.group(1)

        if major not in target_majors:
            continue

        if major not in result or _version_key(tag) > _version_key(result[major]):
            result[major] = tag

    return result


def _version_key(value: str):
    return tuple(int(x) for x in value.split("."))
