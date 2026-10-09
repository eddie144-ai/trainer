---
name: eli5
description: Turn a complex document, PDF, proposal, contract, codebase or concept into a one-page visual explainer with a big diagram, one everyday analogy and very little text. Use when the user says "ELI5", "explain like I'm 5", "explain this simply", "dumb this down", "visual breakdown", "explain this to a client / PM / non-technical person", or asks for a one-page summary of a long document. For money documents (proposals, quotes, invoices, contracts), always show where the money goes.
---

# ELI5: one-page visual explainers

Make one page that a smart 12-year-old could understand in 60 seconds. The diagram does the explaining; the words only label it.

## Step 1: Read and find the one idea

- Read the whole source (file, PDF, folder or topic). For code, trace the main path from entry point to output; skip helpers.
- Write down, privately: **the one sentence that matters most**, the 3–6 parts that make it up, and how they connect (flow, split, layers, before/after, or cycle).
- Pick **one analogy** from everyday life (phone book, kitchen, post office, plumbing, a shop). Use it throughout. Never mix two analogies.

## Step 2: Pick the diagram shape

| The content is… | Draw |
|---|---|
| A process or request path (DNS, auth, checkout, a pipeline) | Left-to-right flow with numbered steps |
| Money or any total split into parts | Stacked bar or proportional blocks with amounts |
| A system with parts | Boxes with labeled arrows, max 6 boxes |
| A choice or comparison | Two or three columns side by side |
| Layers (network stack, architecture) | Stacked horizontal bands |
| Change over time | Timeline |

## Step 3: Build the page

Write a single self-contained `eli5-<topic>.html` file in the current directory (no external scripts or fonts), then tell the user the path. Layout, top to bottom:

1. **Title**: the topic as a plain question ("How does DNS work?").
2. **The one sentence**: large text, under 20 words.
3. **The diagram**: inline SVG, at least half the page. Big labels (16px+), at most 6 main shapes, 2–3 colors plus gray, analogy terms first with the real term small underneath (e.g. "Phone book" / *DNS resolver*).
4. **3–5 "what this means" bullets**, each under 15 words.
5. **"Watch out for"**: one line, only if there's a real catch.

Total visible text, excluding diagram labels: **about 100 words or fewer**. Must read at phone width and in dark mode (`prefers-color-scheme`).

If the user wants a reply in the terminal and no file, draw the diagram in a fenced ASCII block instead and keep the same structure.

## Money documents (proposals, quotes, retainers, contracts)

Always include, computed from the document; never estimated:
- **Monthly total split into its parts** (e.g. $11,000/mo = $4,000 media spend + $7,000 agency fees), drawn as a proportional bar.
- **Annual totals** for each part (monthly × 12, or the contract term if different; state which).
- **"What you keep if you cancel"**: notice period, minimum term, cancellation fees, who owns the ad accounts, creative, data and logins.
- **"Money that leaves vs money that works"**: pass-through spend vs fees.

If a number isn't in the document, write "not stated" rather than inferring it. Show your arithmetic in a small footnote so the reader can check it.

## Code

- Diagram the main request or data path, not the file tree.
- Label boxes with what they do ("checks your password"), with the file or module name small underneath.
- One "where to look first" line pointing at the 1–2 files that matter most.

## Don'ts

- No jargon without the analogy word first.
- No walls of text, no more than one diagram, no decorative icons.
- Don't make up facts, numbers or quotes that aren't in the source.
- Don't talk down to the reader; simple ≠ childish.
