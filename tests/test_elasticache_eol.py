# ruff: file-ignore[call-datetime-without-tzinfo]
from datetime import date
from datetime import datetime as dt
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from aws_generated_data.cli import app
from aws_generated_data.commands.elasticache_eol import (
    CalItem,
    ElastiCacheItem,
    get_elasticache_eol_data,
    parse_elasticache_release_calendar,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import requests_mock
    from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    ("fx_file", "expected"),
    [
        (
            "elasticache-engine-versions.html",
            [
                # versions with extended support; the end of standard support date
                ("Redis OSS v4", dt(2026, 1, 31, 0, 0)),
                ("Redis OSS v5", dt(2026, 1, 31, 0, 0)),
                ("Redis OSS v6", dt(2027, 1, 31, 0, 0)),
                # versions already past EOL
                ("Version 3", dt(2023, 7, 31, 0, 0)),
                ("Version 2", dt(2023, 1, 13, 0, 0)),
            ],
        )
    ],
)
def test_parse_elasticache_release_calendar(
    fx: Callable[[str], str], fx_file: str, expected: list[CalItem]
) -> None:
    assert parse_elasticache_release_calendar(fx(fx_file)) == expected


def test_get_elasticache_eol_data(
    mocker: MockerFixture, requests_mock: requests_mock.Mocker
) -> None:
    m = mocker.patch(
        "aws_generated_data.commands.elasticache_eol.parse_elasticache_release_calendar",
        autospec=True,
        return_value=[("Redis OSS v6", dt(2021, 1, 1))],
    )
    requests_mock.get("https://example.com", text="data")
    assert get_elasticache_eol_data("https://example.com") == [
        ElastiCacheItem(engine="redis", version="6", eol=date(2021, 1, 1))
    ]
    m.assert_called_once_with("data")


#
# cli related tests
#
runner = CliRunner()


def test_cli_elasticache_eol_fetch(tmp_path: Path, mocker: MockerFixture) -> None:
    output_file = tmp_path / "output.yaml"
    # Today is Women Ironman World Championship day in Kona, Hawaii :)
    date_mock = mocker.patch(
        "aws_generated_data.commands.elasticache_eol.datetime",
        autospec=True,
    )
    date_mock.now.return_value.date.return_value = date(2023, 10, 14)
    read_output_file_mock = mocker.patch(
        "aws_generated_data.commands.elasticache_eol.read_output_file",
        autospec=True,
        return_value=[
            ElastiCacheItem(
                engine="manual-added", version="1.2.4", eol=date(2024, 1, 1)
            ),
            ElastiCacheItem(
                engine="obsolete-one", version="1.2.3", eol=date(2023, 10, 12)
            ),
            # previously existing item with an outdated EOL date
            ElastiCacheItem(engine="redis", version="6", eol=date(2025, 1, 1)),
        ],
    )

    get_elasticache_eol_data_mock = mocker.patch(
        "aws_generated_data.commands.elasticache_eol.get_elasticache_eol_data",
        autospec=True,
        return_value=[
            # overwrite the existing item redis:6
            ElastiCacheItem(engine="redis", version="6", eol=date(2024, 1, 1)),
            ElastiCacheItem(engine="redis", version="5", eol=date(2024, 1, 1)),
            ElastiCacheItem(engine="redis", version="4", eol=date(2024, 1, 1)),
        ],
    )
    write_output_file_mock = mocker.patch(
        "aws_generated_data.commands.elasticache_eol.write_output_file", autospec=True
    )
    result = runner.invoke(
        app,
        [
            "elasticache-eol",
            "fetch",
            "--elasticache-release-calendar-url",
            "https://example.com",
            "--output",
            str(output_file),
            "--clean-up-days",
            "2",
        ],
    )
    assert result.exit_code == 0
    read_output_file_mock.assert_called_once_with(output_file, ElastiCacheItem)
    get_elasticache_eol_data_mock.assert_called_once_with("https://example.com")
    write_output_file_mock.assert_called_once_with(
        output_file,
        [
            ElastiCacheItem(engine="redis", version="6", eol=date(2024, 1, 1)),
            ElastiCacheItem(engine="redis", version="5", eol=date(2024, 1, 1)),
            ElastiCacheItem(engine="redis", version="4", eol=date(2024, 1, 1)),
            ElastiCacheItem(
                engine="manual-added", version="1.2.4", eol=date(2024, 1, 1)
            ),
        ],
    )
