# Repository Guidelines

## Project Structure & Module Organization

This repository currently contains planning documents for a greenhouse pepper smart-farm LLM and control system:

- `PLAN.md`: system goals, architecture, safety principles, and phased roadmap.
- `todo.md`: detailed implementation backlog, suitable for conversion into issues.
- `schedule.md`: 8-week execution plan mapped from the backlog.

Keep new project documentation in Markdown at the repository root until a larger structure is introduced. When implementation starts, prefer the structure already proposed in `todo.md`: `docs/` for design notes and ADRs, `data/` for dataset schemas and samples, `experiments/` for model trials, `infra/` for deployment assets, and service directories such as `state-estimator/`, `policy-engine/`, and `llm-orchestrator/`.

## Build, Test, and Development Commands

There is no build system or test runner configured yet. For documentation-only changes, validate Markdown manually before committing:

- `rg "TODO|TBD" *.md`: find unresolved placeholders.
- `sed -n '1,120p' PLAN.md`: preview document sections in the terminal.

When code is added, document the exact local commands here and in `README.md`, for example `pytest`, `npm test`, or `docker compose up`.

## Coding Style & Naming Conventions

Use clear Markdown headings and concise bullet lists. Preserve Korean domain terminology already used in the planning files, and use English identifiers for future machine-readable names.

For future schemas and services, prefer lowercase kebab-case directory names (`policy-engine`) and snake_case identifiers in JSON fields (`zone_id`, `sensor_id`, `action_type`). Keep units explicit in field names or schema descriptions.

## Testing Guidelines

No automated tests exist yet. As implementation begins, add tests next to the relevant service or under a top-level `tests/` directory. Prioritize tests for safety gates, schema validation, policy decisions, and malformed LLM outputs. Name tests by expected behavior, for example `test_blocks_high_risk_action_without_approval`.

## Commit & Pull Request Guidelines

This workspace does not include Git history, so no existing commit convention can be inferred. Use short, imperative commit messages such as `Add policy engine safety checklist` or `Define sensor naming rules`.

Pull requests should include a summary, changed files, validation performed, and any safety or operational impact. Link related issues when available. For architecture changes, include the rationale and update `PLAN.md`, `todo.md`, or `schedule.md` in the same PR.

## Security & Configuration Tips

Do not commit API keys, greenhouse credentials, PLC addresses, or production sensor endpoints. Store environment examples as templates only, such as `.env.example`, with safe placeholder values.
