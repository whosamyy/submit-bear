"""Read-only public GitHub snapshot checks over MCP stdio."""

import re
import json
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

mcp = FastMCP("Bear Fetch")


def repository_name(url: str) -> str:
    """Accept only HTTPS github.com owner/repository URLs, optionally ending .git."""
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.netloc != "github.com"
            or parts.query or parts.fragment):
        raise ValueError("Use https://github.com/OWNER/REPO with no query or fragment.")
    match = re.fullmatch(r"/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)/?", parts.path)
    if not match:
        raise ValueError("Expected a repository URL, not a file or branch URL.")
    owner, repo = match.groups()
    repo = repo.removesuffix(".git")
    if not repo or repo in {".", ".."}:
        raise ValueError("Invalid repository name.")
    return f"{owner}/{repo}"


async def inspect_repo(repo_url: str, required_paths: list[str], ref: str | None,
                       client: httpx.AsyncClient) -> dict:
    """Implementation accepts an injected HTTP client for deterministic tests."""
    result = dict(repository=None, ref=ref, remote_commit_sha=None,
                  checked_at=datetime.now(timezone.utc).isoformat(),
                  found=[], missing=[], unverified=list(required_paths), errors=[],
                  limitations=["Checks regular-file presence only, not contents or correctness."])
    try:
        name = repository_name(repo_url)
        result["repository"] = name
        if len(required_paths) > 100:
            raise ValueError("At most 100 required paths are supported.")
        for path in required_paths:
            if (not path or path.startswith("/") or "\\" in path
                    or any(p in {"", ".", ".."} for p in path.split("/"))
                    or any(ord(c) < 32 for c in path)):
                raise ValueError("Required paths must be relative, exact file paths without traversal.")
        if ref is not None and (not ref.strip() or len(ref) > 256
                                or any(ord(c) < 32 for c in ref)):
            raise ValueError("Ref must be a nonempty branch, tag, or commit identifier.")

        async def get(endpoint: str, **params):
            response = await client.get(f"https://api.github.com/repos/{name}{endpoint}",
                                        params=params)
            if response.status_code != 200:
                code = response.status_code
                if code == 404:
                    message = "Not found or not publicly accessible (repository/ref/object)."
                elif code == 429 or (code == 403 and (
                        response.headers.get("x-ratelimit-remaining") == "0"
                        or "retry-after" in response.headers
                        or "rate limit" in response.text.lower())):
                    message = "GitHub rate limit reached; retry later."
                else:
                    message = "GitHub request failed; no absence can be inferred."
                raise ValueError(f"HTTP {code}: {message}")
            return response.json()

        metadata = await get("")
        if metadata.get("private") is not False:
            raise ValueError("Repository was not confirmed public.")
        selected = ref if ref is not None else metadata["default_branch"]
        result["ref"] = selected
        commit = await get(f"/commits/{quote(selected, safe='')}")
        sha = commit["sha"]
        tree_sha = commit["commit"]["tree"]["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", sha) or not re.fullmatch(r"[0-9a-f]{40}", tree_sha):
            raise ValueError("GitHub returned an invalid commit or tree SHA.")
        result["remote_commit_sha"] = sha
        tree = await get(f"/git/trees/{tree_sha}", recursive="1")
        entries = {item["path"]: item for item in tree["tree"]}
        if not isinstance(tree.get("truncated"), bool):
            raise ValueError("GitHub did not confirm whether the tree is complete.")
        if tree["truncated"]:
            result["limitations"].append("GitHub truncated the tree; unseen paths remain unverified.")
        # Only classify after successful retrieval; failed requests never mean missing.
        result["unverified"] = []
        for path in dict.fromkeys(required_paths):
            item = entries.get(path)
            if item and item.get("type") == "blob" and item.get("mode") in {"100644", "100755"}:
                result["found"].append(path)
            elif item:
                result["unverified"].append(path)
                result["limitations"].append(f"{path}: not a regular file (directory, symlink, or submodule).")
            elif tree["truncated"]:
                result["unverified"].append(path)
            else:
                result["missing"].append(path)
    except httpx.RequestError:
        result["errors"].append("Network request failed or timed out; paths remain unverified.")
    except (json.JSONDecodeError, KeyError, TypeError):
        result["errors"].append("Unexpected GitHub response; verification incomplete.")
    except ValueError as error:
        result["errors"].append(str(error))
    return result


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                                     idempotentHint=True, openWorldHint=True))
async def check_public_repo(repo_url: str, required_paths: list[str], ref: str | None = None) -> dict[str, Any]:
    """Check exact regular-file paths in a public GitHub repository at one remote commit.

    Resolve the default branch unless a branch, tag, or SHA is supplied. Return
    found, missing, and unverified paths plus errors. Failed API requests never
    establish missing files. No credentials, content downloads, or writes.
    """
    async with httpx.AsyncClient(timeout=20, follow_redirects=False, trust_env=False,
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": "Submit-Bear"}) as client:
        return await inspect_repo(repo_url, required_paths, ref, client)


if __name__ == "__main__":
    mcp.run(transport="stdio")
