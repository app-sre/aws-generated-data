# ruff: noqa: DTZ007
import calendar
import logging
import re
from collections.abc import Iterable, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any, Protocol, TypeVar

import requests
import yaml
from pydantic import BaseModel, RootModel, ValidationError, field_validator

MONTH_YEAR = re.compile(r"\w+ \d+")
DAY_MONTH_YEAR = re.compile(r"\d+ \w+ \d+")
MONTH_DAY_YEAR = re.compile(r"\w+ \d+, \d+")
ISO = re.compile(r"\d{4}-\d{2}-\d{2}")

log = logging.getLogger(__name__)

EOLType = TypeVar("EOLType", bound="HasEOL")
ItemType = TypeVar("ItemType")
Root = RootModel[Sequence[Any]]

VERSION_PATTERN = re.compile(r"(?<!\d)(\d+(\.\d+){0,3})(?!\d)")


class HasEOL(Protocol):
    eol: date


class VersionItem(BaseModel):
    version: str
    eol: date

    @field_validator("version", mode="before")
    @classmethod
    def version_remove_asterisk(cls, value: str) -> str:
        # special msk version handling
        if value.endswith(("-tiered", ".x")):
            return value

        if not (match := VERSION_PATTERN.search(value)):
            raise ValueError(f"Invalid version: {value}")
        return match.group()

    def __lt__(self, other: Any) -> bool:  # noqa: ANN401
        if not isinstance(other, VersionItem):
            return False
        return self.version < other.version


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
    if ISO.fullmatch(date_str):
        return datetime.strptime(date_str, "%Y-%m-%d")
    raise ValueError(f"Unknown date format: {date_str}")


def read_output_file(output: Path, item_type: type[ItemType]) -> list[ItemType]:
    try:
        return [
            item_type(**item)
            for item in yaml.safe_load(output.read_text(encoding="utf-8"))
        ]
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
        ),
        encoding="utf-8",
    )


def filter_items(items: Iterable[EOLType], expired_date: date) -> list[EOLType]:
    """Filter items that are not expired."""
    return [item for item in items if item.eol > expired_date]


def http_get(url: str) -> str:
    # AWS blocks Python requests. Use curl's user-agent to bypass the captcha check.
    return requests.get(url, headers={"user-agent": "curl/8.6.0"}, timeout=60).text
