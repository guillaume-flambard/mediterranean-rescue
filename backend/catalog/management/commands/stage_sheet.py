from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from catalog.crosswalk import propose_links, propose_ports, stage_snapshot
from catalog.models import Source
from catalog.sheets import load_contract


class Command(BaseCommand):
    help = "Stage a local Sheets CSV export privately and print proposal counts; never publishes"

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--sheet", required=True, choices=sorted(load_contract()["sheets"]))
        parser.add_argument("--file", required=True)
        parser.add_argument("--actor", required=True, help="username recorded as stager")

    def handle(self, *args, **options):
        limit = load_contract()["input"]["max_bytes"]
        try:
            source = Source.objects.get(key=options["source"])
            actor = get_user_model().objects.get(username=options["actor"])
            path = Path(options["file"])
            if path.stat().st_size > limit:
                raise ValidationError(f"Export exceeds {limit} bytes")
            snapshot, created = stage_snapshot(
                source=source, sheet=options["sheet"], content=path.read_bytes(), actor=actor
            )
        except (Source.DoesNotExist, get_user_model().DoesNotExist) as exc:
            raise CommandError(str(exc)) from exc
        except (OSError, ValidationError, PermissionDenied) as exc:
            raise CommandError(str(exc)) from exc
        proposals = (
            propose_ports(snapshot) if snapshot.sheet == "Data_ports" else propose_links(snapshot)
        )
        counts = {}
        for proposal in proposals:
            counts[proposal.kind] = counts.get(proposal.kind, 0) + 1
        summary = " ".join(f"{kind}={count}" for kind, count in sorted(counts.items()))
        # Counts only: no source value is printed.
        self.stdout.write(
            f"Snapshot {snapshot.pk}; created={created}; rows={snapshot.row_count}; "
            f"read={snapshot.source_read}; {summary}"
        )
