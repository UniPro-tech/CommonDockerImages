from __future__ import annotations

import requests


GITHUB_API = "https://api.github.com"


def get_release_tags(repository: str) -> list[str]:
    url = f"{GITHUB_API}/repos/{repository}/releases"

    params = {
        "per_page": 100,
    }

    tags = []

    while url:
        response = requests.get(
            url,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        releases = response.json()

        for release in releases:
            tag = release.get("tag_name")

            if tag:
                tags.append(tag.lstrip("v"))

        if len(releases) < 100:
            break

        params["page"] = params.get("page", 1) + 1

    return tags
