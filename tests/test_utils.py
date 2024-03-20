from datetime import date
from datetime import datetime as dt
from pathlib import Path

import pytest
import yaml
from pydantic import BaseModel

from aws_generated_data.commands.rds_eol import RdsItem
from aws_generated_data.utils import (
    Root,
    VersionItem,
    filter_items,
    parse_date,
    read_output_file,
    write_output_file,
)


@pytest.mark.parametrize(
    "date_str, expected",
    [
        ("10 January 2021", dt(2021, 1, 10)),
        ("January 10, 2021", dt(2021, 1, 10)),
        ("15 July 1979", dt(1979, 7, 15)),
        ("January 2021", dt(2021, 1, 31)),
        ("September 2021", dt(2021, 9, 30)),
        pytest.param(
            "just an arbitry string",
            None,
            marks=pytest.mark.xfail(strict=True, raises=ValueError),
        ),
    ],
)
def test_parse_date(date_str: str, expected: dt) -> None:
    assert parse_date(date_str) == expected


class EolItem(BaseModel):
    name: str
    eol: date


@pytest.mark.parametrize(
    "items, expired_date, expected",
    [
        (
            [
                EolItem(name="item1", eol=date(2021, 1, 1)),
                EolItem(name="item2", eol=date(2022, 1, 1)),
                EolItem(name="item2", eol=date(2022, 1, 2)),
                EolItem(name="item3", eol=date(2023, 1, 1)),
            ],
            date(2022, 1, 1),
            [
                EolItem(name="item2", eol=date(2022, 1, 2)),
                EolItem(name="item3", eol=date(2023, 1, 1)),
            ],
        ),
    ],
)
def test_filter_items(
    items: list[EolItem], expired_date: date, expected: list[EolItem]
) -> None:
    assert filter_items(items, expired_date) == expected


RDS_ITEMS = [
    RdsItem(engine="something-else", version="1.2.4", eol=date(2021, 1, 1)),
    RdsItem(engine="foobar", version="1.2.3", eol=date(2021, 1, 1)),
]


@pytest.mark.parametrize(
    "output, expected",
    [
        # output does not exist yet
        (None, []),
        # empty file
        ("", []),
        # not a yaml file
        ("garbage", []),
        # another yaml file
        (yaml.dump({"foo": "bar"}), []),
        # another yaml file
        (yaml.dump([{"foo": "bar"}]), []),
        # real yaml file
        (yaml.dump(Root(sorted(RDS_ITEMS, reverse=True)).model_dump()), RDS_ITEMS),
    ],
)
def test_read_output_file(
    tmp_path: Path, output: str | None, expected: list[RdsItem]
) -> None:
    output_file = tmp_path / "output.yaml"
    if output:
        output_file.write_text(output)
    assert read_output_file(output_file, RdsItem) == expected


def test_write_output_file(tmp_path: Path) -> None:
    output_file = tmp_path / "output.yaml"
    write_output_file(output_file, RDS_ITEMS)
    assert read_output_file(output_file, RdsItem) == RDS_ITEMS


@pytest.mark.parametrize(
    "version, eol, expected",
    [
        ("1.2.3", date(2021, 1, 1), VersionItem(version="1.2.3", eol=date(2021, 1, 1))),
        (
            "1.2.3*",
            date(2021, 1, 1),
            VersionItem(version="1.2.3", eol=date(2021, 1, 1)),
        ),
        (
            "*1.2.3*",
            date(2021, 1, 1),
            VersionItem(version="1.2.3", eol=date(2021, 1, 1)),
        ),
        (
            "*1.2.3",
            date(2021, 1, 1),
            VersionItem(version="1.2.3", eol=date(2021, 1, 1)),
        ),
        (
            " 1.2.3  ",
            date(2021, 1, 1),
            VersionItem(version="1.2.3", eol=date(2021, 1, 1)),
        ),
    ],
)
def test_version_item(version: str, eol: date, expected: VersionItem) -> None:
    assert VersionItem(version=version, eol=eol) == expected
