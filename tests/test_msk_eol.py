from collections.abc import Callable
from datetime import date
from datetime import datetime as dt
from pathlib import Path

import pytest
import requests_mock
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from aws_generated_data.cli import app
from aws_generated_data.commands.msk_eol import (
    CalItem,
    get_msk_eol_data,
    parse_msk_release_calendar,
)
from aws_generated_data.utils import VersionItem


@pytest.mark.parametrize(
    "fx_file, expected",
    [
        (
            "supported-kafka-versions.html",
            [
                ("1.1.1", dt(2024, 6, 5, 0, 0)),
                ("2.1.0", dt(2024, 6, 5, 0, 0)),
                ("2.2.1", dt(2024, 6, 8, 0, 0)),
                ("2.3.1", dt(2024, 6, 8, 0, 0)),
                ("2.4.1", dt(2024, 6, 8, 0, 0)),
                ("2.4.1.1", dt(2024, 6, 8, 0, 0)),
                ("2.5.1", dt(2024, 6, 8, 0, 0)),
                ("2.6.0", dt(2024, 9, 11, 0, 0)),
                ("2.6.1", dt(2024, 9, 11, 0, 0)),
                ("2.6.2", dt(2024, 9, 11, 0, 0)),
                ("2.6.3", dt(2024, 9, 11, 0, 0)),
                ("2.7.0", dt(2024, 9, 11, 0, 0)),
                ("2.7.1", dt(2024, 9, 11, 0, 0)),
                ("2.7.2", dt(2024, 9, 11, 0, 0)),
                ("2.8.0", dt(2024, 9, 11, 0, 0)),
                ("2.8.1", dt(2024, 9, 11, 0, 0)),
                ("2.8.2-tiered", dt(2025, 1, 14, 0, 0)),
                ("3.1.1", dt(2024, 9, 11, 0, 0)),
                ("3.2.0", dt(2024, 9, 11, 0, 0)),
                ("3.3.1", dt(2024, 9, 11, 0, 0)),
                ("3.3.2", dt(2024, 9, 11, 0, 0)),
                ("3.4.0", dt(2025, 6, 17, 0, 0)),
            ],
        )
    ],
)
def test_parse_msk_release_calendar(
    fx: Callable[[str], str], fx_file: str, expected: list[CalItem]
) -> None:
    assert parse_msk_release_calendar(fx(fx_file)) == expected


def test_get_msk_eol_data(
    mocker: MockerFixture, requests_mock: requests_mock.Mocker
) -> None:
    m = mocker.patch(
        "aws_generated_data.commands.msk_eol.parse_msk_release_calendar",
        autospec=True,
        return_value=[("1.2.3", dt(2021, 1, 1))],
    )
    requests_mock.get("https://example.com", text="data")
    assert get_msk_eol_data("https://example.com") == [
        VersionItem(version="1.2.3", eol=date(2021, 1, 1))
    ]
    m.assert_called_once_with("data")


#
# cli related tests
#
runner = CliRunner()


def test_cli_msk_eol_fetch(tmp_path: Path, mocker: MockerFixture) -> None:
    output_file = tmp_path / "output.yaml"
    # Today is Women Ironman World Championship day in Kona, Hawaii :)
    date_mock = mocker.patch(
        "aws_generated_data.commands.msk_eol.date",
        autospec=True,
    )
    date_mock.today.return_value = date(2023, 10, 14)
    read_output_file_mock = mocker.patch(
        "aws_generated_data.commands.msk_eol.read_output_file",
        autospec=True,
        return_value=[
            VersionItem(version="1.2.4", eol=date(2023, 10, 13)),
            VersionItem(version="1.2.3", eol=date(2023, 10, 12)),
            # previously existing item with an outdated EOL date
            VersionItem(version="11.1", eol=date(2025, 1, 1)),
        ],
    )

    get_msk_eol_data_mock = mocker.patch(
        "aws_generated_data.commands.msk_eol.get_msk_eol_data",
        autospec=True,
        return_value=[
            # overwrite the existing item 11.1
            VersionItem(version="11.1", eol=date(2024, 1, 1)),
            VersionItem(version="12.2", eol=date(2024, 1, 1)),
            VersionItem(version="8", eol=date(2024, 1, 1)),
            VersionItem(version="5.7", eol=date(2024, 1, 1)),
        ],
    )
    write_output_file_mock = mocker.patch(
        "aws_generated_data.commands.msk_eol.write_output_file", autospec=True
    )
    result = runner.invoke(
        app,
        [
            "msk-eol",
            "fetch",
            "--msk-release-calendar-url",
            "https://example.com",
            "--output",
            str(output_file),
            "--clean-up-days",
            "2",
        ],
    )
    assert result.exit_code == 0
    read_output_file_mock.assert_called_once_with(output_file, VersionItem)
    get_msk_eol_data_mock.assert_called_once_with("https://example.com")
    write_output_file_mock.assert_called_once_with(
        output_file,
        [
            VersionItem(version="8", eol=date(2024, 1, 1)),
            VersionItem(version="5.7", eol=date(2024, 1, 1)),
            VersionItem(version="12.2", eol=date(2024, 1, 1)),
            VersionItem(version="11.1", eol=date(2024, 1, 1)),
            VersionItem(version="1.2.4", eol=date(2023, 10, 13)),
        ],
    )
