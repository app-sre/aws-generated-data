from collections.abc import Callable
from datetime import date
from datetime import datetime as dt
from pathlib import Path

import pytest
import requests_mock
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from aws_generated_data.cli import app
from aws_generated_data.commands.rds_eol import (
    CalItem,
    Engine,
    RdsItem,
    engine_with_url,
    get_rds_eol_data,
    parse_aws_release_calendar,
)


@pytest.mark.parametrize(
    "fx_file, expected",
    [
        (
            "postgresql-release-calendar.html",
            [
                ("16.2", dt(2025, 6, 30, 0, 0)),
                ("16.1", dt(2025, 3, 31, 0, 0)),
                ("15.6", dt(2025, 6, 30, 0, 0)),
                ("15.5", dt(2025, 3, 31, 0, 0)),
                ("15.4", dt(2024, 9, 30, 0, 0)),
                ("15.3", dt(2024, 9, 30, 0, 0)),
                ("15.2", dt(2024, 3, 29, 0, 0)),
                ("14.11", dt(2025, 6, 30, 0, 0)),
                ("14.10", dt(2025, 3, 31, 0, 0)),
                ("14.9", dt(2024, 9, 30, 0, 0)),
                ("14.8", dt(2024, 9, 30, 0, 0)),
                ("14.7", dt(2024, 3, 29, 0, 0)),
                ("14.6", dt(2024, 3, 29, 0, 0)),
                ("14.5", dt(2024, 3, 29, 0, 0)),
                ("14.4", dt(2024, 3, 29, 0, 0)),
                ("14.3", dt(2024, 3, 29, 0, 0)),
                ("13.14", dt(2025, 6, 30, 0, 0)),
                ("13.13", dt(2025, 3, 31, 0, 0)),
                ("13.12", dt(2024, 9, 30, 0, 0)),
                ("13.11", dt(2024, 9, 30, 0, 0)),
                ("13.10", dt(2024, 3, 29, 0, 0)),
                ("13.9", dt(2024, 3, 29, 0, 0)),
                ("13.8", dt(2024, 3, 29, 0, 0)),
                ("13.7", dt(2024, 3, 29, 0, 0)),
                ("12.18", dt(2025, 6, 30, 0, 0)),
                ("12.17", dt(2025, 2, 28, 0, 0)),
                ("12.16", dt(2024, 9, 30, 0, 0)),
                ("12.15", dt(2024, 9, 30, 0, 0)),
                ("12.14", dt(2024, 3, 29, 0, 0)),
                ("12.13", dt(2024, 3, 29, 0, 0)),
                ("12.12", dt(2024, 3, 29, 0, 0)),
                ("12.11", dt(2024, 3, 29, 0, 0)),
                ("11.22*", dt(2024, 2, 29, 0, 0)),
                ("11.21", dt(2024, 2, 29, 0, 0)),
            ],
        ),
        (
            "mysql-release-calendar.html",
            [
                ("8.0.36", dt(2025, 3, 31, 0, 0)),
                ("8.0.35", dt(2025, 3, 31, 0, 0)),
                ("8.0.34", dt(2024, 9, 30, 0, 0)),
                ("8.0.33", dt(2024, 9, 30, 0, 0)),
                ("8.0.32", dt(2024, 9, 30, 0, 0)),
                ("8.0.31", dt(2024, 3, 29, 0, 0)),
                ("8.0.28", dt(2024, 3, 29, 0, 0)),
                ("5.7.44*", dt(2024, 2, 29, 0, 0)),
                ("5.7.43", dt(2024, 2, 29, 0, 0)),
            ],
        ),
    ],
)
def test_parse_aws_release_calendar(
    fx: Callable[[str], str], fx_file: str, expected: list[CalItem]
) -> None:
    assert parse_aws_release_calendar(fx(fx_file)) == expected


def test_get_rds_eol_data(
    mocker: MockerFixture, requests_mock: requests_mock.Mocker
) -> None:
    m = mocker.patch(
        "aws_generated_data.commands.rds_eol.parse_aws_release_calendar",
        autospec=True,
        return_value=[("1.2.3", dt(2021, 1, 1))],
    )
    requests_mock.get("https://example.com", text="data")
    assert get_rds_eol_data(Engine("mysql:https://example.com")) == [
        RdsItem(engine="mysql", version="1.2.3", eol=date(2021, 1, 1))
    ]
    m.assert_called_once_with("data")


def test_get_rds_eol_data_with_asterisk(
    mocker: MockerFixture, requests_mock: requests_mock.Mocker
) -> None:
    m = mocker.patch(
        "aws_generated_data.commands.rds_eol.parse_aws_release_calendar",
        autospec=True,
        return_value=[("1.2.3*", dt(2021, 1, 1))],
    )
    requests_mock.get("https://example.com", text="data")
    assert get_rds_eol_data(Engine("mysql:https://example.com")) == [
        RdsItem(engine="mysql", version="1.2.3", eol=date(2021, 1, 1))
    ]
    m.assert_called_once_with("data")


#
# cli related tests
#
def test_engine_with_url() -> None:
    engine = engine_with_url("mysql:https://example.com:9999/foobar?whatever")
    assert engine.name == "mysql"
    assert engine.url == "https://example.com:9999/foobar?whatever"


runner = CliRunner()


def test_cli_rds_eol_fetch(tmp_path: Path, mocker: MockerFixture) -> None:
    output_file = tmp_path / "output.yaml"
    # Today is Women Ironman World Championship day in Kona, Hawaii
    date_mock = mocker.patch(
        "aws_generated_data.commands.rds_eol.date",
        autospec=True,
    )
    date_mock.today.return_value = date(2023, 10, 14)
    read_output_file_mock = mocker.patch(
        "aws_generated_data.commands.rds_eol.read_output_file",
        autospec=True,
        return_value=[
            RdsItem(engine="manual-added", version="1.2.4", eol=date(2024, 1, 1)),
            RdsItem(
                engine="manual-added-but-not-yet-obsolete",
                version="1.2.4",
                eol=date(2023, 10, 13),
            ),
            RdsItem(engine="obsolete-one", version="1.2.3", eol=date(2023, 10, 12)),
            # previously existing item with an outdated EOL date
            RdsItem(engine="postgres", version="11.1", eol=date(2025, 1, 1)),
        ],
    )

    get_rds_eol_data_mock = mocker.patch(
        "aws_generated_data.commands.rds_eol.get_rds_eol_data",
        autospec=True,
        side_effect=[
            [
                # overwrite the existing item postgres:11.1
                RdsItem(engine="postgres", version="11.1", eol=date(2024, 1, 1)),
                RdsItem(engine="postgres", version="12.2", eol=date(2024, 1, 1)),
            ],
            [
                RdsItem(engine="mysql", version="8", eol=date(2024, 1, 1)),
                RdsItem(engine="mysql", version="5.7", eol=date(2024, 1, 1)),
            ],
        ],
    )
    write_output_file_mock = mocker.patch(
        "aws_generated_data.commands.rds_eol.write_output_file", autospec=True
    )
    result = runner.invoke(
        app,
        [
            "rds-eol",
            "fetch",
            "--engines",
            "postgres:https://example.com/postgres",
            "--engines",
            "mysql:https://example.com/mysql",
            "--output",
            str(output_file),
            "--clean-up-days",
            "2",
        ],
    )
    assert result.exit_code == 0
    read_output_file_mock.assert_called_once_with(output_file, RdsItem)
    get_rds_eol_data_mock.assert_has_calls([
        mocker.call(Engine("postgres:https://example.com/postgres")),
        mocker.call(Engine("mysql:https://example.com/mysql")),
    ])
    write_output_file_mock.assert_called_once_with(
        output_file,
        [
            RdsItem(engine="postgres", version="12.2", eol=date(2024, 1, 1)),
            RdsItem(engine="postgres", version="11.1", eol=date(2024, 1, 1)),
            RdsItem(engine="mysql", version="8", eol=date(2024, 1, 1)),
            RdsItem(engine="mysql", version="5.7", eol=date(2024, 1, 1)),
            RdsItem(
                engine="manual-added-but-not-yet-obsolete",
                version="1.2.4",
                eol=date(2023, 10, 13),
            ),
            RdsItem(engine="manual-added", version="1.2.4", eol=date(2024, 1, 1)),
        ],
    )
