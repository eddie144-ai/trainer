"""Render a ranked match list as a text digest (the email body) and a simple
static HTML page (the local demo — NOT deployed)."""
from __future__ import annotations
import html
from .match import Match


def _fmt_value(m: Match) -> str:
    v = m.tender.value_amount
    return f"£{v:,.0f}" if v else "value not stated"


def text_digest(profile_name: str, matches: list[Match], bar: int = 40,
                limit: int = 10) -> str:
    shown = [m for m in matches if m.score >= bar][:limit]
    lines = [f"ContractRadar digest — {profile_name}",
             f"{len(shown)} opportunities worth your attention "
             f"(from {len(matches)} live tenders)", ""]
    for m in shown:
        t = m.tender
        lines.append(f"[{m.score}] {t.title}")
        lines.append(f"     {t.buyer or 'Unknown buyer'} · {_fmt_value(m)} · "
                     f"closes {t.deadline[:10] if t.deadline else 'n/a'}")
        lines.append(f"     {' · '.join(m.reasons[:3])}")
        lines.append(f"     {t.url}")
        lines.append("")
    if not shown:
        lines.append("(nothing cleared the relevance bar in this batch)")
    return "\n".join(lines)


def html_page(profile_name: str, matches: list[Match], bar: int = 40,
              limit: int = 12) -> str:
    shown = [m for m in matches if m.score >= bar][:limit]
    rows = []
    for m in shown:
        t = m.tender
        band = "#16a34a" if m.score >= 70 else "#ca8a04" if m.score >= 50 else "#6b7280"
        rows.append(f"""
      <article class="card">
        <div class="score" style="background:{band}">{m.score}</div>
        <div class="body">
          <a class="title" href="{html.escape(t.url or '#')}" target="_blank" rel="noopener">{html.escape(t.title or '')}</a>
          <div class="meta">{html.escape(t.buyer or 'Unknown buyer')} · {_fmt_value(m)} · closes {t.deadline[:10] if t.deadline else 'n/a'}</div>
          <ul class="reasons">{''.join(f'<li>{html.escape(r)}</li>' for r in m.reasons[:4])}</ul>
        </div>
      </article>""")
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ContractRadar — {html.escape(profile_name)}</title>
<style>
  :root {{ color-scheme: light dark; --bg:#f7f7f8; --card:#fff; --ink:#111; --muted:#555; --line:#e5e7eb; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg:#0c0c0d; --card:#161618; --ink:#f3f3f3; --muted:#a1a1aa; --line:#27272a; }} }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }}
  .wrap {{ max-width:760px; margin:0 auto; padding:32px 16px 64px; }}
  h1 {{ font-size:22px; margin:0 0 4px; }}
  .sub {{ color:var(--muted); margin:0 0 24px; }}
  .card {{ display:flex; gap:14px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; margin-bottom:12px; }}
  .score {{ flex:0 0 42px; height:42px; border-radius:9px; color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center; }}
  .title {{ font-weight:600; color:var(--ink); text-decoration:none; }}
  .title:hover {{ text-decoration:underline; }}
  .meta {{ color:var(--muted); font-size:14px; margin:3px 0 6px; }}
  .reasons {{ margin:0; padding-left:18px; color:var(--muted); font-size:13px; }}
  .foot {{ color:var(--muted); font-size:13px; margin-top:28px; border-top:1px solid var(--line); padding-top:14px; }}
</style></head>
<body><div class="wrap">
  <h1>ContractRadar</h1>
  <p class="sub">Matched UK public contracts for <strong>{html.escape(profile_name)}</strong> ·
     {len(shown)} worth a look, ranked by fit · live Contracts Finder data</p>
  {''.join(rows) or '<p>Nothing cleared the relevance bar in this batch.</p>'}
  <p class="foot">Demo built on real Contracts Finder (OCDS, Open Government Licence v3.0) data.
     Relevance scoring by ContractRadar. Not affiliated with GOV.UK.</p>
</div></body></html>"""
