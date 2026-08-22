# Publication safety

This repository is designed to be public without exposing employer or private-project information.

## Controls

- All committed records are synthetic.
- Generated databases and output files are ignored by Git.
- The repository contains no broker account, MetaTrader configuration, employer export, private screenshot, or AI service credential.
- `scripts/audit_publication.py` scans every tracked text file for common secret formats, local private paths, forbidden configuration names, and credential assignments.
- GitHub Actions runs the audit before tests and sample execution.

The scanner is a guardrail, not a guarantee. Renato still reviews the exact Git diff before any public push.

## Safe reuse of real experience

The project reuses only the general professional problem: metadata can be incomplete, duplicated, inconsistent, or ambiguous. The implementation, rules, sample data, dashboard, and documentation were created independently for this portfolio.
