from __future__ import annotations

import requests


DOCKER_HUB_API = "https://hub.docker.com/v2/repositories"


def get_tags(repository: str) -> list[str]:
    """
    Docker Hub repository のタグ一覧を取得する。

    Docker Hub API の全ページを無制限に辿るのではなく、
    next URL がなくなるまで取得する。

    403/429 が発生した場合は、レスポンス内容を含めて
    分かりやすいエラーを出す。
    """

    url = f"{DOCKER_HUB_API}/{repository}/tags/"

    params = {
        "page_size": 100,
    }

    tags: list[str] = []

    session = requests.Session()

    while url:
        response = session.get(
            url,
            params=params if "?" not in url else None,
            timeout=30,
            headers={
                "Accept": "application/json",
                "User-Agent": "CommonDockerImages/1.0",
            },
        )

        if response.status_code == 403:
            raise RuntimeError(
                "Docker Hub API returned 403 Forbidden.\n"
                f"URL: {response.url}\n"
                "Docker Hub API rate limit or access restriction "
                "may have been reached."
            )

        if response.status_code == 429:
            raise RuntimeError(
                "Docker Hub API returned 429 Too Many Requests.\n"
                f"URL: {response.url}\n"
                "Please retry later or authenticate against Docker Hub."
            )

        response.raise_for_status()

        data = response.json()

        for result in data.get("results", []):
            name = result.get("name")

            if name:
                tags.append(name)

        url = data.get("next")

        # next URLが返ってきた場合は、そのURLをそのまま使う
        params = None

    return tags
