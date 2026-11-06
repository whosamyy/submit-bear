# Submit Bear 🧸

Submit Bear is a little pre-submission checker I made for my coding projects. I kept running into the same situation where the code looked finished, but I wasn't totally sure whether the docs were updated, what had actually been tested, or whether the version on GitHub was the latest one.

There are two parts: **Bear Inspector**, a Codex skill that reviews a project, and **Bear Fetch**, a Python MCP server that checks a public GitHub repo. The name is mostly for fun, but the bear's mood also gives a quick summary of the inspection.

## Why I made it

I went back through my prompt logs from previous homework assignments. A few things kept coming up:

> "have u been updating prompt log"  
> — [HW7 Sonar Diver prompt log](https://github.com/whosamyy/hw7-coop-card-game/blob/main/prompt_log.md), around line 957

> "Do not claim browser testing passed unless you actually tested it in a browser"  
> — HW7 Sonar Diver prompt log, around line 632

> "Do not rewrite unrelated code"  
> — HW6 Idea Originality Checker prompt log, around line 1640

The first one was an actual case where a prompt hadn't been logged yet. The other two are instructions I kept emphasizing, not proof that the agent definitely broke those rules. Still, it made me want a separate checker instead of repeatedly reminding the same coding agent what to look for.

I also wanted to catch something a local code review can't reliably tell me: whether the files I think I submitted are actually on GitHub. That's why I made the MCP part.

## What each part does

### Bear Inspector (the skill)

The skill lives at `.agents/skills/bear-inspector/SKILL.md`. I call it with `$bear-inspector` in Codex, usually in a new conversation after doing the coding in a different session.

It reads the requirements, code, documentation, available testing evidence, and local Git state. The report uses **COMPLETE**, **MISSING**, and **UNVERIFIED**, with file/line evidence and the next thing to check. It is read-only: it doesn't quietly edit the project for me.

An important distinction is that something can be **missing from the full spec** but **outside the scope of the current submission**. For example, my One Bullet Phase 1 project deliberately didn't include enemies or scoring yet. The checker should mention those features without treating them as Phase 1 failures.

I also added three bear moods:

- `ʕ－ᴥ－ʔ 💤` Sleeping Bear — required checks look complete.
- `ʕ•́ᴥ•̀ʔ 🥺` Worried Bear — something important still needs verification.
- `ʕಥᴥಥʔ 💧` Crying Bear — a required submission item is confirmed missing.

The mood is just a quick summary. The evidence in the table matters more.

### Bear Fetch (the MCP server)

`bear_fetch/server.py` is a local Python MCP server using stdio. It exposes one tool:

```text
check_public_repo(repo_url, required_paths, ref=None)
```

It accepts a **public GitHub repo**, resolves the requested ref (or the default branch), gets the remote commit SHA, and checks whether specific regular-file paths exist at that commit. It returns found, missing, and unverified paths, plus errors and limitations.

Bear Fetch checks **file presence, not whether the contents are good**. It also doesn't know my local commit by itself. Codex can compare the remote SHA it returns against local `git rev-parse HEAD` when I ask for a push-status check.

## Installation (Codex + macOS)

The setup below is what I tested. Other agent clients may use different skill directories or MCP config formats.

1. Clone the repository and install the Python dependencies:

   ```bash
   git clone https://github.com/whosamyy/submit-bear.git
   cd submit-bear
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. For the skill, open this repository as the workspace in Codex so it can find `.agents/skills/bear-inspector/SKILL.md`. To use the skill from other workspaces, copy the `bear-inspector` folder into that project's `.agents/skills/` directory (or your Codex user-level skills directory).

3. Register Bear Fetch in `~/.codex/config.toml`. **Replace `/ABSOLUTE/PATH/submit-bear` with the actual folder on your computer.** These paths are machine-specific, and the virtual environment needs to exist first.

   ```toml
   [mcp_servers.bear-fetch]
   command = "/ABSOLUTE/PATH/submit-bear/.venv/bin/python"
   args = ["/ABSOLUTE/PATH/submit-bear/bear_fetch/server.py"]
   enabled = true
   startup_timeout_sec = 30
   ```

4. Restart Codex and use a **fresh local session**. You don't need to manually leave `server.py` running; Codex starts the stdio server when it needs it.

5. In Codex, try something like:

   ```text
   $bear-inspector
   Inspect /absolute/path/to/my-project against its SPEC.md.
   The public repo is https://github.com/OWNER/REPO.
   Use Bear Fetch for remote verification. Don't modify files.
   ```

   Or test the MCP tool by itself:

   ```text
   Use the actual Bear Fetch check_public_repo MCP tool on
   https://github.com/OWNER/REPO.
   Check README.md and requirements.txt and return the remote SHA.
   Do not substitute a web search.
   ```

For repeatable automated tests, I used the tests in `tests/test_bear_fetch.py`. With the virtual environment active:

```bash
python -m pytest tests/test_bear_fetch.py
```

## What I tested

I confirmed the skill was discoverable with a small smoke test, then tested real audits on [One Bullet](https://github.com/whosamyy/one-bullet) and [Sonar Diver](https://github.com/whosamyy/hw7-coop-card-game). Bear Fetch passed 10 local automated tests, including MCP initialization/tool invocation, and I later confirmed that Codex could call the registered MCP tool in an actual local session. See [DEMONSTRATION.md](DEMONSTRATION.md) for the specific results and [ITERATION.md](ITERATION.md) for the things that went wrong.

Limitations: It only works on public GitHub repos, GitHub requests can fail or hit rate limits, and reading code is not the same as running it in a browser. A good-looking report is not a guarantee that a submission will get full credit.

## What I used / AI usage

I used the [15-114 HW8 instructions](https://www.cs.cmu.edu/~113/hw8.html), the [Agent Skills format](https://agentskills.io/), the [Codex skills/config documentation](https://developers.openai.com/codex/skills), and the [official MCP documentation](https://modelcontextprotocol.io/) as references. The read-only checking idea is related to the course's `spec-check` example, but I extended it to testing evidence, Git status, assignment scope, and a separate GitHub tool.

I used ChatGPT to help plan the workflow, come up with staged Codex prompts, and draft these Markdown write-ups. I used Codex to implement and revise the skill/MCP server. The testing outcomes here are taken from my real Codex sessions, not tests ChatGPT ran on my computer. I decided what the checker should focus on and reviewed its reports to decide what needed changing.