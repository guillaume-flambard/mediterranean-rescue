"""Prove invalid frontend operations fail generation, rather than trusting happy-path codegen."""

import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".graphql",
    prefix="contract-negative-",
    dir=root / "frontend/src",
    delete=False,
) as output:
    output.write("query InvalidContractProof { events { items { fieldThatMustNotExist } } }\n")
    target = Path(output.name)
try:
    result = subprocess.run(
        ["pnpm", "codegen"], cwd=root / "frontend", capture_output=True, text=True
    )
    if result.returncode == 0 or "fieldThatMustNotExist" not in result.stdout + result.stderr:
        raise SystemExit("FAIL: invalid operation was not rejected for the intended reason")
    print("PASS: GraphQL Code Generator rejects an unknown frontend field")
finally:
    target.unlink()
