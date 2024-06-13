import logging
from datetime import (
    date,
    datetime,
    timedelta,
)
from pathlib import Path
from typing import Annotated

import requests
import typer
from bs4 import BeautifulSoup

from aws_generated_data.utils import (
    VersionItem,
    filter_items,
    parse_date,
    read_output_file,
    write_output_file,
)

app = typer.Typer()
log = logging.getLogger(__name__)

CalItem = tuple[str, datetime]


def parse_msk_release_calendar(page: str) -> list[CalItem]:
    items: list[CalItem] = []
    soup = BeautifulSoup(page, "html5lib")
    # the first table is the one we want
    version_table = soup.find("table")
    if not version_table:
        raise RuntimeError("Failed to find version table")

    for row in version_table.find_all("tr"):  # type: ignore
        cols = row.find_all("td")
        if len(cols) == 3:  # noqa: PLR2004
            date_str = cols[2].text.strip()
            if date_str == "--":
                continue
            try:
                items.append((cols[0].text.strip(), parse_date(date_str)))
            except ValueError:
                # skip invalid dates
                pass

    return items


def get_msk_eol_data(msk_release_calendar_url: str) -> list[VersionItem]:
    version_page = requests.get(msk_release_calendar_url)
    return [
        VersionItem(version=version, eol=d.date())
        for version, d in parse_msk_release_calendar(version_page.text)
    ]


@app.command()
def fetch(
    msk_release_calendar_url: Annotated[
        str,
        typer.Option(
            envvar="AGD_MSK_RELEASE_CALENDAR_URL",
            help="Url to the MSK release calendar",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            help="Output file",
            envvar="AGD_MSK_EOL_OUTPUT",
        ),
    ],
    clean_up_days: Annotated[
        int,
        typer.Option(
            help="Remove items older than this number of days",
            envvar="AGD_MSK_CLEAN_UP_DAYS",
        ),
    ] = 365,
) -> None:
    """Fetch RDS EOL data from AWS and saves it to a file."""
    msk_items_dict = {
        item.version: item for item in read_output_file(output, VersionItem)
    }
    log.info(f"Processing {msk_release_calendar_url} ...")
    for item in get_msk_eol_data(msk_release_calendar_url):
        msk_items_dict[item.version] = item

    msk_items = filter_items(
        msk_items_dict.values(),
        expired_date=date.today() - timedelta(days=clean_up_days),
    )
    write_output_file(output, sorted(msk_items, reverse=True))
