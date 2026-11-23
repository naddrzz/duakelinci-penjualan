# CLAUDE.md

@AGENTS.md

## Claude Code notes

- Canonical project map, business rules, change matrix, and JIT search commands live in [AGENTS.md](AGENTS.md) and are loaded above via `@AGENTS.md`.
- Always run `python -m pytest` before concluding any task (`42` tests covering CSV cleaning, exact unrounded `Q1` math, SKU & salesman attribution, custom CSV upload/reset with zero hardcoded leakage, and HTTP routes).
- Keep all rendered UI and Telegram summary copy in **Bahasa Indonesia**; keep code, identifiers, commit messages, and documentation in **English** unless the user requests otherwise in chat.
- Never hardcode sample dataset strings (months, regions, branches, salesmen, outlet names/IDs, or SKUs) in templates, CSS, or JS — every view must render dynamically from `app.state.report`.
- Preserve 100% offline execution (`Dockerfile` non-root `appuser`, self-hosted variable fonts/logos/favicons, zero external requests, stdlib multipart upload parsing).
