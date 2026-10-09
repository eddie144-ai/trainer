# Claude Code toolkit

Personal Claude Code config, kept here so it survives between sessions. These files are **not** used by this repo's app.

- `CLAUDE.md`: tool-routing rules and verified install commands. Goes in `~/.claude/CLAUDE.md`.
- `skills/eli5/SKILL.md`: the ELI5 one-page visual explainer skill. Goes in `~/.claude/skills/eli5/`.

## Install

```bash
cp claude-toolkit/CLAUDE.md ~/.claude/CLAUDE.md      # or append if you already have one
mkdir -p ~/.claude/skills/eli5
cp claude-toolkit/skills/eli5/SKILL.md ~/.claude/skills/eli5/SKILL.md
```

Restart Claude Code, then try `ELI5 how DNS works`.
