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


class RdsItem(VersionItem):
    engine: str

    def __lt__(self, other: Any) -> bool:  # noqa: ANN401
        if not isinstance(other, RdsItem):
            return False
        return (self.engine, self.version) < (other.engine, other.version)


CalItem = tuple[str, datetime]


class Engine:  # noqa: PLW1641
    def __init__(self, value: str) -> None:
        self.name, self.url = value.split(":", maxsplit=1)
        match self.name:
            case "mysql":
                self.section_id = "MySQL.Concepts.VersionMgmt.Supported"
                self.table_limit = 2
            case "postgres":
                self.section_id = "PostgreSQL.Concepts.VersionMgmt.Supported"
                self.table_limit = 1
            case "aurora-postgresql":
                self.section_id = "aurorapostgresql.minor.versions.supported"
                self.table_limit = 1
            case _:
                raise ValueError(f"Unsupported engine name: {self.name}")

    def __str__(self) -> str:
        return f"<Engine: {self.name=} {self.url=}>"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Engine):
            return False
        return (self.name, self.url) == (other.name, other.url)


def engine_with_url(value: str) -> Engine:
    return Engine(value)


def parse_aws_release_calendar(page: str, engine: Engine) -> list[CalItem]:
    items: list[CalItem] = []
    soup = BeautifulSoup(page, "html5lib")

    if not (minor_version_section := soup.find(id=engine.section_id)):
        raise RuntimeError("Failed to find minor version section")

    # the first table in the minor version section is the one we want
    if not (
        version_tables := minor_version_section.find_all_next(
            "table", limit=engine.table_limit
        )
    ):
        raise RuntimeError("Failed to find version table")

    for table in version_tables:
        table = cast(Tag, table)
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 4:  # noqa: PLR2004
                with contextlib.suppress(ValueError):
                    items.append((
                        cols[0].text.strip(),
                        parse_date(cols[3].text.strip()),
                    ))

    if not items:
        raise RuntimeError("Failed to find any version items")
    return items


def get_rds_eol_data(engine: Engine) -> list[RdsItem]:
    version_page = http_get(engine.url)
    return [
        RdsItem(engine=engine.name, version=version, eol=d.date())
        for version, d in parse_aws_release_calendar(version_page, engine)
    ]


@app.command()
def fetch(
    engines: Annotated[
        list[Engine],
        typer.Option(
            parser=engine_with_url,
            envvar="AGD_RDS_EOL_ENGINES",
            help="Engines to sync; format: engine_name:release_calendar_url",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            help="Output file",
            envvar="AGD_RDS_EOL_OUTPUT",
        ),
    ],
    clean_up_days: Annotated[
        int,
        typer.Option(
            help="Remove items older than this number of days",
            envvar="AGD_RDS_CLEAN_UP_DAYS",
        ),
    ] = 1095,
) -> None:
    """Fetch RDS EOL data from AWS and saves it to a file."""
    rds_items_dict = {
        (item.engine, item.version): item for item in read_output_file(output, RdsItem)
    }
    for engine in engines:
        log.info(f"Processing {engine} ...")
        for item in get_rds_eol_data(engine):
            rds_items_dict[item.engine, item.version] = item

    rds_items = filter_items(
        rds_items_dict.values(),
        expired_date=datetime.now(tz=UTC).date() - timedelta(days=clean_up_days),
    )
    write_output_file(output, sorted(rds_items, reverse=True))
