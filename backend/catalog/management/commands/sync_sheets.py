"""Reads the configured Google Sheets tabs once, or every N seconds with --every (ADR 0012)."""

import json
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.sync import sync_actor, sync_all


class Command(BaseCommand):
    help = "Read the Google Sheets exports and save new data privately; nothing is published."

    def add_arguments(self, parser):
        parser.add_argument(
            "--config",
            default=settings.SHEETS_SYNC_CONFIG,
            help="JSON file: source key and tab URLs",
        )
        parser.add_argument("--every", type=int, default=0, help="Repeat every N seconds (0: once)")

    def handle(self, *args, config, every, **options):
        if not config:
            raise CommandError("No sync configuration: set SHEETS_SYNC_CONFIG or pass --config.")
        settings_file = Path(config)
        if not settings_file.is_file():
            raise CommandError("The sync configuration file does not exist.")
        conf = json.loads(settings_file.read_text(encoding="utf-8"))
        actor = sync_actor()
        while True:
            for run in sync_all(conf, actor=actor):
                # Status and counts only: source values never reach the logs.
                self.stdout.write(
                    f"{run.sheet}: {run.status} {json.dumps(run.summary)} {run.message}".rstrip()
                )
            if every <= 0:
                return
            time.sleep(every)
