# Personal Claude Code toolkit

Install location: `~/.claude/CLAUDE.md` (loads in every session, every project).

## How to pick a tool

When I ask for help:
1. Name the best-fit tool from the routing table below in one line, then do the work.
2. Prefer a built-in command or an installed plugin over suggesting a new install.
3. If two tools overlap, pick the most specific one. Never stack tools that do the same job.
4. If the tool I need isn't installed, give me the exact install command from this file and continue with the closest built-in. Never guess an install command or package name that isn't listed here.

## Routing table

| When I say… | Use | Notes |
|---|---|---|
| "Set up this project", "what automations do I need" | **claude-code-setup** | Prompt: "Recommend automations for this project. Keep review read-only." |
| "Remember my stack", "stop making me re-explain" | **`/init`** → this project's `CLAUDE.md` | Add claude-mem only if `CLAUDE.md` isn't enough |
| "Map this codebase", "how does X work", "find dependencies" | **Graphify** | `/graphify`, `/graphify query "how does X work"` |
| "Plan this feature", "spec first", "full dev cycle" | **Agent Skills** | `/spec` → `/plan` → `/build` → `/test` → `/review` → `/ship`. I run each step myself; nothing ships automatically. |
| "Review this PR / diff", "find bugs" | **`/code-review`** (built-in) or **code-review** plugin | `/security-review` for anything touching auth, input or secrets |
| "Simplify / clean up this code" | **`/simplify`** (built-in) or Agent Skills `/code-simplify` | |
| "Claude writes too much code" | **PonyTail** | Shapes the code as it's written; it doesn't post-process |
| "Context too big", "reduce input tokens" | **`/compact`** first, then **Headroom** | Headroom is a proxy: all traffic passes through it |
| "Make this UI not look generic", "pick a design direction" | **frontend-design** | |
| "More experimental / less boring design" | **Taste** | |
| "Audit / polish this UI", "check accessibility" | **Impeccable** | `/impeccable audit`, `/impeccable polish` |
| "Make it look like Stripe / Linear / Notion" | **awesome-design-md** | Copy the brand's `DESIGN.md` into the project, then build against it |
| "Scrape / analyze this page" | **Firecrawl MCP** | |
| "Test this site", "screenshot", "fill this form" | **Playwright MCP** | Never against production without asking me first |
| "Explain this simply", "ELI5", "dumb this down for a client" | **eli5** skill | One-page visual explainer |
| "I keep doing this manually" | **Task Observer**, or a hook via `/hooks` | |

## Install commands (verified)

```bash
# Official Anthropic marketplace (built in to Claude Code)
/plugin install claude-code-setup@claude-plugins-official
/plugin install frontend-design@claude-plugins-official
/plugin install code-review@claude-plugins-official

# Agent Skills (Addy Osmani)
/plugin marketplace add addyosmani/agent-skills
/plugin install agent-skills@addy-agent-skills

# Claude-Mem (optional; try CLAUDE.md first)
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem

# Design
npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"
npx impeccable install                      # repo: pbakaus/impeccable
# awesome-design-md: copy files from github.com/VoltAgent/awesome-design-md

# Workflow
npx skills add rebelytics/one-skill-to-rule-them-all --skill task-observer

# Read the README before installing these (third-party; they hook prompts or proxy traffic)
# Graphify:  pip install graphifyy
# Headroom:  github.com/riicodespretty/headroom-claude-plugin
# PonyTail:  github.com/DietrichGebert/ponytail

# MCP servers (Claude Code uses `claude mcp add`, not claude_desktop_config.json)
claude mcp add playwright -- npx @playwright/mcp@latest
claude mcp add firecrawl -e FIRECRAWL_API_KEY=$FIRECRAWL_API_KEY -- npx -y firecrawl-mcp
```

## Rules

- **Only one token-saving tool at a time.** Headroom, PonyTail and similar skills all inject context on every prompt and can conflict.
- **Never commit API keys.** Pass them with `-e` from environment variables; keep them out of `.mcp.json` in git.
- **Proxies (Headroom, OmniRoute) see all my prompts and code.** Run them locally only.
- **Before running an install command** that isn't in this file, show it to me and say where it came from.

## Not yet verified (don't install or recommend)

Output Optimizer, Second-Brain, img2threejs (two competing repos), Agent Reach, Perplexity MCP (package name unconfirmed), Composio (CLI changes often; use composio.dev docs), Creator Graphics, Thumbnail Strategist, YouTube Optimizer, Competitor Intelligence, Video Postmortem, OmniRoute (works, but routes to non-Claude models), Prompt Master (it writes prompts for other AI tools).
