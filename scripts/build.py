import subprocess
import os
import sys


def main():
    if len(sys.argv) != 4:
        print("Usage: python build.py <major_version> <pg_version> <pg_bigm_version>")
        sys.exit(1)

    major = sys.argv[1]
    pg_version = sys.argv[2]
    bigm_version = sys.argv[3]

    repo_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "your_username").lower()
    image_name = f"ghcr.io/{repo_owner}/postgres-pg-bigm"

    # 常に最新のメジャーバージョンに更新されるタグと、詳細な固定バージョンのタグを生成
    tags = [f"{image_name}:{major}", f"{image_name}:{pg_version}-bigm{bigm_version}"]

    build_context = os.path.join(
        os.path.dirname(__file__), "..", "official", "postgres"
    )

    # --build-arg でバージョンを指定してビルド
    build_cmd = ["docker", "build"]
    build_cmd.extend(["--build-arg", f"PG_VERSION={pg_version}"])
    build_cmd.extend(["--build-arg", f"PG_BIGM_VERSION={bigm_version}"])

    for tag in tags:
        build_cmd.extend(["-t", tag])
    build_cmd.append(build_context)

    print(f"Running build for major version {major}: {' '.join(build_cmd)}")
    subprocess.run(build_cmd, check=True)

    # 生成したタグをプッシュ
    for tag in tags:
        print(f"Pushing: {tag}")
        subprocess.run(["docker", "push", tag], check=True)


if __name__ == "__main__":
    main()
