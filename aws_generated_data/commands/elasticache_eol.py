import contextlib
import logging
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from pathlib import Path
from typing import Annotated, Any, cast

import typer
from bs4 import BeautifulSoup, Tag

from aws_generated_data.utils import (
    VersionItem,
    filter_items,
    http_get,
    parse_date,
    read_output_file,
    write_output_file,
)

app = typer.Typer()
log = logging.getLogger(__name__)

# AWS publishes an EOL schedule for the Redis OSS engine only. Valkey and Memcached
# versions are listed on the same page, but without any EOL dates.
ENGINE = "redis"
# "ElastiCache versions for Redis OSS end of life schedule"
EOL_SECTION_ID = "deprecated-engine-versions"
# the section holds two tables: the extended support schedule and the past EOL versions
EOL_TABLE_LIMIT = 2
# "Major Engine Version | End of Standard Support | Start of Extended Support Y1/Y2/Y3
#  Premium | End of Extended Support and version EOL"
EXTENDED_SUPPORT_COLS = 6
# "Source Major Version | Source Minor Versions | Recommended Upgrade Target | EOL Date"
PAST_EOL_COLS = 4


class ElastiCacheItem(VersionItem):
    engine: str

    def __lt__(self, other: Any) -> bool:  # ruff: ignore[any-type]
        if not isinstance(other, ElastiCacheItem):
            return False
        return (self.engine, self.version) < (other.engine, other.version)


CalItem = tuple[str, datetime]


def parse_elasticache_release_calendar(page: str) -> list[CalItem]:
    items: list[CalItem] = []
    soup = BeautifulSoup(page, "html5lib")

    if not (eol_section := soup.find(id=EOL_SECTION_ID)):
        raise RuntimeError("Failed to find EOL section")

    if not (
        version_tables := eol_section.find_all_next("table", limit=EOL_TABLE_LIMIT)
    ):
        raise RuntimeError("Failed to find version table")

    for table in version_tables:
        table = cast("Tag", table)
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == EXTENDED_SUPPORT_COLS:
                # the end of standard support, like the RDS calendars report
                date_col = cols[1]
            elif len(cols) == PAST_EOL_COLS:
                date_col = cols[3]
            else:
                continue
            with contextlib.suppress(ValueError):
                items.append((
                    cols[0].text.strip(),
                    parse_date(date_col.text.strip()),
                ))

    if not items:
        raise RuntimeError("Failed to find any version items")
    return items


def get_elasticache_eol_data(
    elasticache_release_calendar_url: str,
) -> list[ElastiCacheItem]:
    version_page = http_get(elasticache_release_calendar_url)
    return [
        ElastiCacheItem(engine=ENGINE, version=version, eol=d.date())
        for version, d in parse_elasticache_release_calendar(version_page)
    ]


@app.command()
def fetch(
    elasticache_release_calendar_url: Annotated[
        str,
        typer.Option(
            envvar="AGD_ELASTICACHE_RELEASE_CALENDAR_URL",
            help="Url to the ElastiCache release calendar",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            help="Output file",
            envvar="AGD_ELASTICACHE_EOL_OUTPUT",
        ),
    ],
    clean_up_days: Annotated[
        int,
        typer.Option(
            help="Remove items older than this number of days",
            envvar="AGD_ELASTICACHE_CLEAN_UP_DAYS",
        ),
    ] = 1095,
) -> None:
    """Fetch ElastiCache EOL data from AWS and saves it to a file."""
    elasticache_items_dict = {
        (item.engine, item.version): item
        for item in read_output_file(output, ElastiCacheItem)
    }
    log.info(f"Processing {elasticache_release_calendar_url} ...")
    for item in get_elasticache_eol_data(elasticache_release_calendar_url):
        elasticache_items_dict[item.engine, item.version] = item

    elasticache_items = filter_items(
        elasticache_items_dict.values(),
        expired_date=datetime.now(tz=UTC).date() - timedelta(days=clean_up_days),
    )
    write_output_file(output, sorted(elasticache_items, reverse=True))
