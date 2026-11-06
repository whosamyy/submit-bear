
# Submit Bear — Iteration

Submit Bear didn't work perfectly the first time. I ran into a registration problem with the MCP server, then found an outdated instruction in the skill during an actual project audit. Later I also changed how it labels unfinished but intentionally deferred features.

## 1. Bear Fetch worked locally but wasn't available in Codex

My Python server passed its local tests, including MCP initialization and tool discovery. But when I opened a new Codex chat and asked it to call `check_public_repo`, Codex said there was no Bear Fetch tool available. So a working Python server by itself wasn't enough.

The problem was the registration, not the GitHub-checking code. I initially tried `codex mcp add` in the VS Code terminal, but `codex` wasn't on my shell PATH. I then tried setting it up through configuration, and the first Codex session still couldn't see it.

When I had Codex inspect `~/.codex/config.toml`, it found that `bear-fetch` wasn't actually listed. I added the correct stdio entry pointing to the Python interpreter inside my project's `.venv` and `bear_fetch/server.py`, restarted Codex, and opened a fresh local session.

**Retest:** Codex successfully invoked the real `check_public_repo` tool on One Bullet. It returned the correct remote SHA, found three real files, and marked my deliberately fake filename missing. I didn't have to rewrite the MCP server.

## 2. The first combined audit found an outdated skill instruction

After that, I ran Bear Inspector and Bear Fetch together on One Bullet. The actual MCP call worked, but the agent noticed something in `SKILL.md` that I'd forgotten to update:

> "Bear Fetch is not currently implemented"

That instruction had made sense before I finished the MCP server. It was wrong after registration, though, and could easily make a future checker skip remote verification even when the tool was available. The first run happened to call Bear Fetch anyway because the skill had a separate conditional instruction permitting it.

I updated the skill so that it now says to **call Bear Fetch when the actual MCP tool is available**, and to mark remote information **UNVERIFIED** when it isn't. I also made it explicit that a remote file being present doesn't prove its content is correct, and that local Git status by itself isn't remote evidence.

**Retest:** I opened another fresh Codex session and reran the One Bullet audit at the same commit, `39e9a2c9e5f3e669e704a3285a869321ffca79c5`. The skill loaded, `mcp__bear_fetch__check_public_repo` was invoked, the local and remote SHAs matched, and the report still kept browser testing **UNVERIFIED**. That was the behavior I actually wanted.

This was the clearest before/after change to the **skill itself**, not just MCP setup.

## 3. Fixing the difference between missing and out of scope

I ran more inspections after adding the bear mood display. One version labeled enemies, health, and scoring **UNVERIFIED** in One Bullet, even though those systems were obviously not in the code. The uncertainty wasn't about whether they existed; it was about whether the full spec or just Phase 1 was due.

I changed the skill's rules to keep those two questions separate:

- If a feature is definitely absent, label it **MISSING**.
- If it was explicitly deferred from the current submission, show **MISSING — outside Phase 1 scope** and don't treat it as a mandatory blocker.
- Use **UNVERIFIED** for things where there really isn't enough evidence, like browser testing or missing assignment instructions.

I kept the same bear moods. Missing work that is explicitly outside the assignment scope shouldn't make the bear cry. A genuinely required missing file should.

**Retest:** The next fresh One Bullet inspection listed AC8–13 and the enemy-survival portion of AC7 as **MISSING — outside Phase 1 scope**. It showed **Worried Bear** (`ʕ•́ᴥ•̀ʔ 🥺`), not Crying Bear, because browser tests and course-level submission requirements were still unverified. Bear Fetch still confirmed the GitHub commit and file paths.

## What I'd improve next

Right now Submit Bear is best at identifying gaps in the available **evidence**. It can't prove a browser game works without someone actually testing it, and it needs the correct assignment scope to judge what's mandatory. In the future, I could supply a standardized assignment checklist with each audit or add a way to attach test results to a specific commit. I don't want the skill to start giving an easy "ready" just because the README sounds confident.

The main lesson for me was that getting an agent to use a tool is different from just writing the tool, and that instructions can become wrong as a project changes. Having a separate checking session is what helped me catch that.