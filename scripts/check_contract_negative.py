"""Prove generated REST types reject invalid frontend use at compile time."""

import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".ts", prefix="contract-negative-", dir=root / "frontend/src", delete=False
) as output:
    output.write(
        'import createClient from "openapi-fetch";\nimport type { paths, components } from "./api/schema";\nconst client = createClient<paths>();\nclient.GET("/api/v1/fieldThatMustNotExist/");\nclient.GET("/api/v1/events/", { params: { query: { unknownParameter: true } } });\ndeclare const event: components["schemas"]["Event"];\nevent.fieldThatMustNotExist;\nconst count: number = event.people;\n'
    )
    target = Path(output.name)
try:
    result = subprocess.run(
        ["pnpm", "typecheck"], cwd=root / "frontend", capture_output=True, text=True
    )
    diagnostic = result.stdout + result.stderr
    expected = ["fieldThatMustNotExist", "unknownParameter", "null"]
    if result.returncode == 0 or any(word not in diagnostic for word in expected):
        raise SystemExit(
            "FAIL: invalid endpoint, parameter, field or nullable assignment not rejected: "
            + diagnostic
        )
    print(
        "PASS: generated REST types reject unknown route, parameter, field and unsafe null assignment"
    )
finally:
    target.unlink()
