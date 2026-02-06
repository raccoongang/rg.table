"""Management command to download and import GeoNames data."""

import urllib.request
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from geodata.models import GeoName

# GeoNames download URLs
GEONAMES_BASE_URL = "https://download.geonames.org/export/dump/"
DATASETS = {
    "cities500": "cities500.zip",  # ~200K cities with pop > 500
    "cities1000": "cities1000.zip",  # ~150K cities with pop > 1000
    "cities5000": "cities5000.zip",  # ~50K cities with pop > 5000
    "cities15000": "cities15000.zip",  # ~25K cities with pop > 15000
    "allCountries": "allCountries.zip",  # ~12M all features
}


class Command(BaseCommand):
    help = "Download and import GeoNames data"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dataset",
            type=str,
            default="cities500",
            choices=list(DATASETS.keys()),
            help="Dataset to import (default: cities500)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of records to import (0 = no limit)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before import",
        )

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        dataset = options["dataset"]
        limit = options["limit"]
        clear = options["clear"]

        if clear:
            self.stdout.write("Clearing existing data...")
            GeoName.objects.all().delete()

        filename = DATASETS[dataset]
        url = f"{GEONAMES_BASE_URL}{filename}"

        self.stdout.write(f"Downloading {url}...")
        data = self._download_and_extract(url, filename)

        self.stdout.write("Parsing and importing data...")
        count = self._import_data(data, limit)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully imported {count:,} records")
        )

    def _download_and_extract(self, url: str, filename: str) -> str:
        """Download zip file and extract the txt file."""
        response = urllib.request.urlopen(url)  # noqa: S310
        zip_data = BytesIO(response.read())

        with zipfile.ZipFile(zip_data) as zf:
            # The txt file has the same name as zip but with .txt extension
            txt_filename = Path(filename).stem + ".txt"
            return zf.read(txt_filename).decode("utf-8")

    def _import_data(self, data: str, limit: int) -> int:
        """Parse and import GeoNames data."""
        batch_size = 5000
        records = []
        count = 0

        for line in data.split("\n"):
            if not line.strip():
                continue

            fields = line.split("\t")
            if len(fields) < 19:
                continue

            try:
                record = GeoName(
                    geonameid=int(fields[0]),
                    name=fields[1][:200],
                    asciiname=fields[2][:200],
                    latitude=float(fields[4]) if fields[4] else 0,
                    longitude=float(fields[5]) if fields[5] else 0,
                    feature_class=fields[6][:1] if fields[6] else "",
                    feature_code=fields[7][:10] if fields[7] else "",
                    country_code=fields[8][:2] if fields[8] else "",
                    admin1_code=fields[10][:20] if fields[10] else "",
                    population=int(fields[14]) if fields[14] else 0,
                    elevation=int(fields[15]) if fields[15] else None,
                    timezone=fields[17][:40] if fields[17] else "",
                    modification_date=self._parse_date(fields[18]),
                )
                records.append(record)
                count += 1

                if count % batch_size == 0:
                    self._bulk_save(records)
                    records = []
                    self.stdout.write(f"  Imported {count:,} records...")

                if limit and count >= limit:
                    break

            except (ValueError, IndexError) as e:
                self.stderr.write(f"Skipping invalid record: {e}")
                continue

        # Save remaining records
        if records:
            self._bulk_save(records)

        return count

    def _bulk_save(self, records: list[GeoName]) -> None:
        """Bulk save records with upsert."""
        with transaction.atomic():
            GeoName.objects.bulk_create(
                records,
                update_conflicts=True,
                unique_fields=["geonameid"],
                update_fields=[
                    "name", "asciiname", "latitude", "longitude",
                    "feature_class", "feature_code", "country_code",
                    "admin1_code", "population", "elevation", "timezone",
                    "modification_date",
                ],
            )

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse date string from GeoNames format."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
