
# Submit Bear — Demonstrations

I tried Submit Bear on two of my real HW7 repositories instead of making a fake example. In both cases, the code was originally produced in earlier work, and I used fresh Codex conversations for the checks. I kept everything read-only because I wanted to know what the checker would catch on its own.

## Run 1: One Bullet (HW7 Phase 1)

**Project:** [whosamyy/one-bullet](https://github.com/whosamyy/one-bullet)  
**Local folder:** `/Users/whosamy/Documents/hw7-one-bullet`  
**Commit inspected:** `39e9a2c9e5f3e669e704a3285a869321ffca79c5`

One Bullet is a small browser game where you only have one bullet. After firing, you have to go pick it up before you can shoot again. This was a Phase 1 handoff, so enemies, health, and scoring were intentionally left for later.

I first tested Bear Inspector alone in a fresh session. It read `SPEC.md`, `README.md`, the prompt log, source files, tests, and local Git history. It found the core shooting/retrieval code, but it wouldn't accept source code or README claims as proof of actual browser testing. It also said the remote push was unverified, which was correct because it hadn't used Bear Fetch yet.

Next I registered Bear Fetch and verified that Codex could invoke it. My direct MCP test used:

```text
Tool: bear-fetch.check_public_repo
Repo: https://github.com/whosamyy/one-bullet
Paths: SPEC.md, README.md, prompt_log.md,
       definitely-not-a-real-file.txt
```

The actual response reported `main` at `39e9a2c9e5f3e669e704a3285a869321ffca79c5`, with the first three paths **found** and the fake path **missing**. There were no errors or unverified paths.

Then I ran the full checker in a fresh Codex chat using `$bear-inspector` and asked it to use Bear Fetch. This is a shortened excerpt of its output:

```text
Bear Inspector loaded: Yes
Bear Fetch invoked: mcp__bear_fetch__check_public_repo
Local HEAD matches remote: Yes
Overall readiness: Readiness unverified
```

It marked the Phase 1 mechanics as supported by code inspection. More importantly, it did **not** treat the unfinished full-game systems as automatic blockers for a Phase 1 handoff. The main gaps were evidence for `node --test`, a browser playthrough, and the complete course submission checklist.

I agreed with the overall result. I know the Phase 1 implementation was intentionally limited, but I also couldn't point to a revision-linked browser test from that audit. I liked that it said **UNVERIFIED** rather than pretending it had tested the game.

There was one problem in the toolkit, though. At the end of this first combined run the agent noted that my skill still contained the instruction:

> "Bear Fetch is not currently implemented"

That was outdated by this point. I fixed it and did a separate retest, described in [ITERATION.md](ITERATION.md).

## Run 2: Sonar Diver (HW7 Phase 2)

**Project:** [whosamyy/hw7-coop-card-game](https://github.com/whosamyy/hw7-coop-card-game)  
**Local folder:** `/Users/whosamy/Documents/hw7-coop-card-game`  
**Commit inspected:** `ac72e409861c540db922d153a675b8a1f2573174`

Sonar Diver was more complicated: it was an inherited game with 21 acceptance criteria, and my Phase 2 work added/fixed things within a limited time. I wanted to see if the checker would handle a longer spec without treating every future feature as something I was supposed to have finished.

This time I separated the work into **two fresh Codex sessions**.

### Session A — MCP call

I asked an agent to call the actual `check_public_repo` MCP tool for the Sonar Diver repo. The saved output included:

```json
{
  "repository": "whosamyy/hw7-coop-card-game",
  "ref": "main",
  "remote_commit_sha": "ac72e409861c540db922d153a675b8a1f2573174",
  "found": ["spec.md", "README.md", "prompt_log.md", "HANDOFF_REPORT.md"],
  "missing": [],
  "unverified": [],
  "errors": [],
  "limitations": ["Checks regular-file presence only, not contents or correctness."]
}
```

The invocation returned `isError: false`. There was no fallback to curl or web search, and no files were changed.

### Session B — independent checker

I started another new Codex session, provided Session A's result, and invoked `$bear-inspector`. I asked it to inspect all 21 acceptance criteria, check the documentation, compare local and remote commits, and independently verify the previous agent's GitHub findings.

It loaded the skill and made **another real Bear Fetch call**, rather than just trusting the JSON I pasted. Its results matched Session A and local HEAD. It also checked additional remote paths, including `game.js`, `index.html`, `style.css`, and an asset file.

Some examples from the report:

| Check | Result | Why |
| --- | --- | --- |
| #20 abilities | COMPLETE (code inspection) | Boost/Blink/Shield logic and cooldown handling were present. |
| #16 online co-op | MISSING | No synchronized multiplayer; this was deferred work. |
| #21 difficulty progression | MISSING | No four-tier progression system yet. |
| Browser/audio behavior | UNVERIFIED | No systematic browser/listening results tied to that commit. |
| Remote GitHub files and SHA | COMPLETE | Actual MCP result agreed with local HEAD. |

The checker also noticed documentation questions like original-author credit and prompt/model provenance. I thought those were useful catches because they aren't things I normally think about when checking whether a game runs.

I agreed that Sonar Diver wasn't fully implemented, but I **didn't** agree with interpreting every missing game feature as a failed HW7 submission requirement. The Phase 2 task was to extend an inherited project within a limited time and document what remained. The checker ultimately made that distinction in its final report.

## What I took away

Both projects showed the same useful behavior: the checker cited actual files, separated code inspection from runtime testing, and used Bear Fetch to verify the published commit instead of assuming local Git meant everything was pushed. Sonar Diver also showed why the assignment scope matters as much as the full spec.

The checker did **not** run the browser games or independently prove that every feature worked. That limitation is real, and the reports say so. The independent sessions and exact commit SHAs made the results much easier for me to trust.