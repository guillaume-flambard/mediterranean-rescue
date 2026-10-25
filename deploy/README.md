# Deploying Mediterranean Rescue

One image, `ghcr.io/memolabs-dev/mediterranean-rescue`, built from the root [`Dockerfile`](../Dockerfile) and published by CI for every green commit on `main`. It runs:

- `web` (default command `serve`): applies migrations, then gunicorn serves the API, the admin and the built frontend (WhiteNoise, with a strict Content-Security-Policy);
- `sync_logbook --every 21600` and `sync_sheets --every 300`: the two scheduled readers, same image, another command.

[`compose.yaml`](compose.yaml) is a complete reference stack with PostGIS. Put a proxy that terminates TLS in front of `web`.

## Settings (`deploy/.env`, never committed)

| Variable | Value |
| --- | --- |
| `DJANGO_SECRET_KEY` | at least 50 random characters |
| `DJANGO_ALLOWED_HOSTS` | the public host name, e.g. `rescue.example.org` |
| `CSRF_TRUSTED_ORIGINS` | `https://` + that host |
| `DJANGO_BEHIND_TLS_PROXY` | `1` when the proxy terminates TLS and always sets `X-Forwarded-Proto` |
| `DJANGO_NUM_PROXIES` | number of proxies setting `X-Forwarded-For` (usually `1`) |
| `POSTGRES_ADMIN_PASSWORD`, `DB_PASSWORD` | two different random passwords |
| `DATA_MODE` | `production` (or `training` for fictitious data only) |

`deploy/sheets-sync.json` (mounted into the Sheets reader, never committed) names the source key and the CSV export address of each tab:

```json
{"source": "sos-sheets", "tabs": {"Data_operations": "https://docs.google.com/spreadsheets/d/<id>/export?format=csv&gid=0"}}
```

## First start

```sh
docker compose -f deploy/compose.yaml --env-file deploy/.env up -d
docker compose -f deploy/compose.yaml exec web uv run --no-sync python backend/manage.py createsuperuser
```

Then, in the admin, record the source's publication agreement (who agreed, when, under which terms) before anything from it can be published. Publishing a spreadsheet that its owner already publishes, in one recorded decision ([ADR 0016](../docs/decisions/0016-public-demo-and-sheet-publication.md)):

```sh
docker compose -f deploy/compose.yaml exec web uv run --no-sync python backend/manage.py publish_source --source sos-sheets --actor <username> --reason "<why>"          # dry run, exact counts
docker compose -f deploy/compose.yaml exec web uv run --no-sync python backend/manage.py publish_source --source sos-sheets --actor <username> --reason "<why>" --apply
```

## Operations

- Health: `GET /api/health/` (checks the database). The image has a Docker healthcheck on it.
- Backups: dump the `rescue` database nightly (`pg_dump -Fc`) and test a restore.
- Rollback: run the previous image tag (`ghcr.io/memolabs-dev/mediterranean-rescue:<commit sha>`). Migrations only add; check the release notes before going back across one.
- `/admin/` has no rate limit of its own: restrict it at the proxy (address list or rate limit).
