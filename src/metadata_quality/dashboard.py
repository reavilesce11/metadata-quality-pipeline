"""Generate a dependency-free HTML summary for portfolio review."""

from __future__ import annotations

from collections import Counter
from html import escape
from pathlib import Path

from .quality import QualityIssue


def write_dashboard(
    path: Path,
    total_records: int,
    status_counts: Counter[str],
    issues: list[QualityIssue],
) -> None:
    issue_counts = Counter(issue.issue_code for issue in issues)
    issue_rows = "\n".join(
        f"<tr><td>{escape(code.replace('_', ' ').title())}</td><td>{count}</td></tr>"
        for code, count in sorted(issue_counts.items(), key=lambda item: (-item[1], item[0]))
    )
    review_rate = 0.0 if total_records == 0 else 100 * status_counts["REVIEW"] / total_records
    rejected_rate = 0.0 if total_records == 0 else 100 * status_counts["REJECTED"] / total_records
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Metadata Quality Report</title>
  <style>
    :root {{ color-scheme: dark; --bg:#08111f; --panel:#101c2e; --line:#243753; --text:#f3f7ff; --muted:#9bb0cc; --green:#2ee6a6; --amber:#ffbd59; --red:#ff6b7a; --blue:#67a8ff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font:16px/1.5 Inter,Segoe UI,sans-serif; background:radial-gradient(circle at top left,#163259 0,#08111f 44%); color:var(--text); }}
    main {{ width:min(1040px,calc(100% - 32px)); margin:48px auto; }}
    .eyebrow {{ color:var(--blue); letter-spacing:.18em; text-transform:uppercase; font-size:12px; font-weight:700; }}
    h1 {{ margin:.35rem 0 .5rem; font-size:clamp(32px,6vw,58px); line-height:1.05; }}
    .lead {{ max-width:760px; color:var(--muted); font-size:18px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:32px 0; }}
    .card,.panel {{ background:rgba(16,28,46,.9); border:1px solid var(--line); border-radius:18px; box-shadow:0 18px 45px rgba(0,0,0,.24); }}
    .card {{ padding:22px; }} .card strong {{ display:block; font-size:34px; }} .card span {{ color:var(--muted); }}
    .accepted strong {{ color:var(--green); }} .review strong {{ color:var(--amber); }} .rejected strong {{ color:var(--red); }}
    .panels {{ display:grid; grid-template-columns:1.25fr .75fr; gap:14px; }}
    .panel {{ padding:24px; }} h2 {{ margin-top:0; }}
    table {{ width:100%; border-collapse:collapse; }} th,td {{ text-align:left; padding:12px 8px; border-bottom:1px solid var(--line); }} th {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.1em; }}
    .flow {{ display:grid; gap:10px; }} .flow div {{ padding:13px 14px; border-radius:12px; background:#0b1626; border-left:4px solid var(--blue); }}
    footer {{ margin-top:24px; color:var(--muted); font-size:13px; }}
    @media (max-width:760px) {{ .grid {{ grid-template-columns:repeat(2,1fr); }} .panels {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<main>
  <div class="eyebrow">Synthetic portfolio project · Audit-ready</div>
  <h1>Metadata Quality Report</h1>
  <p class="lead">Clear cases are automated. Ambiguous cases keep their evidence and move to a human review queue instead of being silently guessed.</p>
  <section class="grid">
    <article class="card"><strong>{total_records}</strong><span>Total records</span></article>
    <article class="card accepted"><strong>{status_counts['ACCEPTED']}</strong><span>Accepted</span></article>
    <article class="card review"><strong>{status_counts['REVIEW']}</strong><span>Human review · {review_rate:.0f}%</span></article>
    <article class="card rejected"><strong>{status_counts['REJECTED']}</strong><span>Rejected · {rejected_rate:.0f}%</span></article>
  </section>
  <section class="panels">
    <article class="panel">
      <h2>Why records need attention</h2>
      <table><thead><tr><th>Issue</th><th>Count</th></tr></thead><tbody>{issue_rows}</tbody></table>
    </article>
    <article class="panel">
      <h2>Decision flow</h2>
      <div class="flow">
        <div>1 · Preserve raw provider values</div>
        <div>2 · Normalize comparison keys</div>
        <div>3 · Validate structural rules</div>
        <div>4 · Match canonical episodes</div>
        <div>5 · Route uncertainty to a person</div>
        <div>6 · Persist every reason in SQLite</div>
      </div>
    </article>
  </section>
  <footer>No employer data or private workflow is used. Every row in this demonstration is synthetic.</footer>
</main>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")

