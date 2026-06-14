# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal productivity dashboard for a Synology NAS that synthesizes Google Calendar events, Notion notes, and AI-generated analysis (via Google Gemini 2.5 Flash) into a dark glassmorphic web UI. The "3D Temporal Context Model" produces past retrospective, current focus, and future defensive-alert reports in Chinese.

The stack is deliberately minimal: a single Python backend script generates a JSON file that a vanilla JS/HTML/CSS frontend consumes. There is no build system, no framework, and no test suite.

## Running the Backend

```bash
# Install dependencies (first time only)
./venv/bin/pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib requests

# Run the data sync and AI report generation
./venv/bin/python update_data.py
```

Output: `dashboard/data.json` containing parsed events, reminders, and the Gemini-generated report.

On the NAS, this runs automatically via `/etc/crontab` at 11:00 and 16:00 daily. Logs go to `cron_run.log`.

## Required Credentials

All three of these must be present before `update_data.py` will produce a useful result:

| File / Variable | Purpose |
|---|---|
| `.env` (from `.env.example`) | `NOTION_API_KEY`, `NOTION_PAGE_ID`, `GEMINI_API_KEY` |
| `client_secret.json` | Google Cloud OAuth client credentials |
| `token.json` | Authorized Google Calendar token (auto-refreshed) |

The script loads `.env` manually (no `python-dotenv`); environment variables set before invocation take precedence.

## Architecture: Data Flow

```
Google Calendar API ──┐
                      ├─► update_data.py ─► Gemini 2.5 Flash ─► AI report
Notion API ───────────┘         │
                                └─► dashboard/data.json
                                          │
                                          ▼
                               dashboard/app.js (fetch + render)
```

`update_data.py` does everything in sequence inside `main()`:
1. Fetch Google Calendar (60-day window: −30 to +30 days from now)
2. Fetch Notion page block children
3. Parse and categorize both into `events[]` and `reminders[]`
4. Inject hardcoded dependency links between specific events/reminders
5. Call Gemini with a structured Chinese prompt; retry up to 3× with exponential backoff on 429/500/503
6. Write the combined result to `dashboard/data.json`

## Categorization

`categorize_title()` in `update_data.py` matches Chinese keywords against the event title (case-insensitive). Categories and their keywords are hardcoded and highly personal:

- **work** (`公務專案`): 評選, 會議, 監造, 橋, 分署, etc.
- **family** (`家庭生活`): ck, 學費, 籃球, 石宸睿, 楊準, etc.
- **health** (`健康醫療`): 藥, 診所, 超音波, 鄭維鈞, 張鳳林, etc.
- **admin** (`財務雜務`): 貸款, 扣款, 保費, 管理費, etc.
- Default fallback is `"work"` when no keyword matches.

## Dependency Engine

The dependency links in `update_data.py` (after categorization) are hardcoded relationships that connect specific events to specific Notion reminders. They are keyed on Chinese title substrings and sometimes specific dates (e.g., `2026-06-16`). When adding new recurring dependencies, follow the same pattern: search `notion_reminders` by `content` substring, then `append` to `ev['dependencies']`.

## Frontend

`dashboard/app.js` is a single-file vanilla JS app. Key points:
- Fetches `data.json` with a cache-busting timestamp query parameter (`?v=<Date.now()>`)
- Two views toggled by `switchView()`: `"timeline"` (events + reminders sidebar) and `"ai"` (AI report only)
- Category filtering via `filterCategory()` — switching to AI view first switches back to timeline
- `highlightReminder()` / `highlightEventByDependency()` handle bidirectional click-to-scroll linking between timeline events and reminder cards
- `parseMarkdown()` is a custom line-by-line Markdown→HTML parser supporting headers, lists, blockquotes, tables, and `**bold**`

## Deployment on Synology NAS

- Project root on NAS: `/volume1/web/calendar-dashboard/`
- Web Station serves the `dashboard/` subfolder on port `8085` via Nginx
- Tailscale is used for remote access instead of opening router ports
- Synology's system Python may be 3.8 — the venv isolates the dependency versions
- Crontab on Synology requires actual **TAB** characters (not spaces) between columns in `/etc/crontab`; restart with `sudo systemctl restart crond` after editing

## Modifying Category Keywords

Edit the `work_keywords`, `family_keywords`, `health_keywords`, and `admin_keywords` lists in `categorize_title()` (`update_data.py:122–136`). Keywords are matched with `in title_lower`, so partial Chinese string matching works naturally.

## Modifying the AI Prompt

The Gemini prompt is assembled in `generate_ai_report()` (`update_data.py:154–185`). It instructs Gemini to act as a Chinese-language "chief life and work advisor" and produce a three-layer Markdown report (past/present/future). The model is `gemini-2.5-flash` called via the REST API directly (`generativelanguage.googleapis.com/v1beta`).
