from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from catalog.imports import apply_batch, stage_payload
from catalog.models import Source


class Command(BaseCommand):
    help = "Stage a local canonical JSON file; optionally create drafts, never publish"

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--file", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        try:
            source = Source.objects.get(key=options["source"])
            path = Path(options["file"])
            if path.stat().st_size > 5 * 1024 * 1024:
                raise ValidationError("Import exceeds 5 MiB")
            batch, created = stage_payload(source=source, content=path.read_bytes())
            count = apply_batch(batch_id=batch.pk) if options["apply"] else 0
        except (Source.DoesNotExist, OSError, ValidationError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            f"Batch {batch.pk}; created={created}; drafts_created={count}; status={batch.status}"
        )
