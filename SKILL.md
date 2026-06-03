---
name: synology-ai-calendar-dashboard
description: >-
  Deploys a 3D cognitive calendar and Notion dashboard on a Synology NAS,
  with daily crontab updates and Tailscale secure remote access.
---

# Synology AI Calendar Dashboard Deployment Skill

## Overview
This skill allows an agent to deploy a premium, dark-glassmorphic personal dashboard on a Synology NAS. The dashboard synthesizes Google Calendar events (past 30 to future 30 days) and Notion notes into a "3D Temporal Context Model" (Past Retrospective, Current Focus, Future Defensive Alerts) using Gemini API, updating automatically twice daily.

## Dependencies
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib
- requests

## Quick Start
1. Place `update_data.py`, `.env` (with keys populated), `client_secret.json`, and `token.json` into `/volume1/web/calendar-dashboard/` on the NAS.
2. Put the `dashboard/` folder under the same directory.
3. Configure `crontab` on the NAS using:
   `0 11,16 * * * ericstone cd /volume1/web/calendar-dashboard && ./venv/bin/python update_data.py > cron_run.log 2>&1`
4. Set up a Web Station static portal pointing to `/volume1/web/calendar-dashboard/dashboard` on port `8085`.

## Utility Scripts
The system runs `update_data.py` to synchronize data.
Command:
```bash
./venv/bin/python update_data.py
```
Outputs:
- Generates `dashboard/data.json` containing events, reminders, and the AI advisory report.

## Common Mistakes
1. **Wrong Python Version**: Synology DSM package Python might be older (like 3.8). Make sure dependencies are compatible.
2. **Incorrect Crontab Syntax**: Synology cron requires actual **TAB** characters (not spaces) between columns in `/etc/crontab`.
3. **Mismatched Web Station Folder**: Ensure Web Station's document root points to the `dashboard/` subfolder, not the parent folder, so `index.html` is at the root.
