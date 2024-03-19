import calendar
import logging
import re
from collections.abc import Iterable, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any, Protocol, TypeVar

import yaml
from pydantic import RootModel, ValidationError

MONTH_YEAR = re.compile(r"\w+ \d+")
DAY_MONTH_YEAR = re.compile(r"\d+ \w+ \d+")
MONTH_DAY_YEAR = re.compile(r"\w+ \d+, \d+")

log = logging.getLogger(__name__)

EOLType = TypeVar("EOLType", bound="HasEOL")
ItemType = TypeVar("ItemType")
Root = RootModel[Sequence[Any]]


class HasEOL(Protocol):
    eol: date


def parse_date(date_str: str) -> datetime:
    if MONTH_YEAR.fullmatch(date_str):
        d = datetime.strptime(date_str, "%B %Y")
        # a date like "March 2022" means actually "March 31, 2022"
        last_day_of_month = calendar.monthrange(d.year, d.month)[1]
        return d.replace(day=last_day_of_month)
    if DAY_MONTH_YEAR.fullmatch(date_str):
        return datetime.strptime(date_str, "%d %B %Y")
    if MONTH_DAY_YEAR.fullmatch(date_str):
        return datetime.strptime(date_str, "%B %d, %Y")
    raise ValueError(f"Unknown date format: {date_str}")


def read_output_file(output: Path, item_type: type[ItemType]) -> list[ItemType]:
    try:
        return [item_type(**item) for item in yaml.safe_load(output.read_text())]
    except (TypeError, FileNotFoundError, ValidationError):
        log.warning(f"Failed to load {output}")
        return []


def write_output_file(output: Path, items: Sequence[Any]) -> None:
    log.info(f"Saving to {output} ...")
    output.write_text(
        yaml.dump(
            Root(items).model_dump(),
            explicit_start=True,
            indent=2,
            default_flow_style=False,
        )
    )


def filter_items(items: Iterable[EOLType], expired_date: date) -> list[EOLType]:
    """Filter items that are not expired."""
    return [item for item in items if item.eol > expired_date]
