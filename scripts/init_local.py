"""Generate development-only secrets without printing them or replacing an existing file."""

import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    print("Existing .env preserved")
else:
    content = "DJANGO_ENV=development\nDJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver\nDATA_MODE=production\n"
    for key in ["DJANGO_SECRET_KEY", "POSTGRES_ADMIN_PASSWORD", "DB_PASSWORD"]:
        content += f"{key}={secrets.token_urlsafe(50)}\n"
    with target.open("x") as output:
        output.write(content)
    target.chmod(0o600)
    print("Local .env created with private permissions; no data seeded")
