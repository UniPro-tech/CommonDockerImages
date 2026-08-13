from __future__ import annotations

import requests


DOCKERHUB_API = "https://hub.docker.com/v2/repositories"


def get_tags(repository: str) -> list[str]:
    url = f"{DOCKERHUB_API}/{repository}/tags/"
    params = {
        "page_size": 100,
    }

    versions = []

    while url:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        for result in data.get("results", []):
            versions.append(result["name"])

        url = data.get("next")
        params = None

    return versions
