from collections.abc import Callable
from datetime import date
from datetime import datetime as dt
from pathlib import Path

import pytest
import requests_mock
import yaml
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from aws_generated_data.cli import app
from aws_generated_data.commands.rds_eol import (
    CalItem,
    Engine,
    RdsEol,
    RdsItem,
    engine_with_url,
    get_rds_eol_data,
    parse_aws_release_calendar,
    parse_date,
    read_output_file,
    write_output_file,
)


@pytest.mark.parametrize(
    "fx_file, expected",
    [
        (
            "postgresql-release-calendar.html",
            [
                ("15.4", dt(2024, 9, 1, 0, 0)),
                ("15.3", dt(2024, 9, 1, 0, 0)),
                ("15.2", dt(2024, 3, 1, 0, 0)),
                ("14.9", dt(2024, 9, 1, 0, 0)),
                ("14.8", dt(2024, 9, 1, 0, 0)),
                ("14.7", dt(2024, 3, 1, 0, 0)),
                ("14.6", dt(2024, 3, 1, 0, 0)),
                ("14.5", dt(2024, 3, 1, 0, 0)),
                ("14.4", dt(2024, 3, 1, 0, 0)),
                ("14.3", dt(2024, 3, 1, 0, 0)),
                ("13.12", dt(2024, 9, 1, 0, 0)),
                ("13.11", dt(2024, 9, 1, 0, 0)),
                ("13.10", dt(2024, 3, 1, 0, 0)),
                ("13.9", dt(2024, 3, 1, 0, 0)),
                ("13.8", dt(2024, 3, 1, 0, 0)),
                ("13.7", dt(2024, 3, 1, 0, 0)),
                ("12.16", dt(2024, 9, 1, 0, 0)),
                ("12.15", dt(2024, 9, 1, 0, 0)),
                ("12.14", dt(2024, 3, 1, 0, 0)),
                ("12.13", dt(2024, 3, 1, 0, 0)),
                ("12.12", dt(2024, 3, 1, 0, 0)),
                ("12.11", dt(2024, 3, 1, 0, 0)),
                ("11.21", dt(2023, 11, 1, 0, 0)),
                ("11.20", dt(2023, 11, 1, 0, 0)),
                ("11.19", dt(2023, 11, 1, 0, 0)),
                ("11.18", dt(2023, 11, 1, 0, 0)),
                ("11.17", dt(2023, 11, 1, 0, 0)),
                ("11.16", dt(2023, 11, 1, 0, 0)),
            ],
        ),
        (
            "mysql-release-calendar.html",
            [
                ("8.0.34", dt(2024, 9, 1, 0, 0)),
                ("8.0.33", dt(2024, 9, 1, 0, 0)),
                ("8.0.32", dt(2024, 3, 1, 0, 0)),
                ("8.0.31", dt(2024, 3, 1, 0, 0)),
                ("8.0.30", dt(2023, 9, 1, 0, 0)),
                ("8.0.28", dt(2024, 3, 1, 0, 0)),
                ("5.7.43", dt(2023, 12, 1, 0, 0)),
                ("5.7.42", dt(2023, 12, 1, 0, 0)),
                ("5.7.41", dt(2023, 12, 1, 0, 0)),
                ("5.7.40", dt(2023, 12, 1, 0, 0)),
                ("5.7.39", dt(2023, 12, 1, 0, 0)),
                ("5.7.38", dt(2023, 12, 1, 0, 0)),
                ("5.7.37", dt(2023, 12, 1, 0, 0)),
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


@pytest.mark.parametrize(
    "date_str, expected",
    [
        ("10 January 2021", dt(2021, 1, 10)),
        ("30 September 1979", dt(1979, 9, 30)),
        ("January 2021", dt(2021, 1, 1)),
        ("September 2021", dt(2021, 9, 1)),
        pytest.param(
            "just an arbitry string",
            None,
            marks=pytest.mark.xfail(strict=True, raises=ValueError),
        ),
    ],
)
def test_parse_date(date_str: str, expected: dt) -> None:
    assert parse_date(date_str) == expected


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
        (yaml.dump(RdsEol(sorted(RDS_ITEMS, reverse=True)).model_dump()), RDS_ITEMS),
    ],
)
def test_read_output_file(
    tmp_path: Path, output: str | None, expected: list[RdsItem]
) -> None:
    output_file = tmp_path / "output.yaml"
    if output:
        output_file.write_text(output)
    assert read_output_file(output_file) == expected


def test_write_output_file(tmp_path: Path) -> None:
    output_file = tmp_path / "output.yaml"
    write_output_file(output_file, RDS_ITEMS)
    assert read_output_file(output_file) == RDS_ITEMS


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
        ],
    )
    get_rds_eol_data_mock = mocker.patch(
        "aws_generated_data.commands.rds_eol.get_rds_eol_data",
        autospec=True,
        side_effect=[
            [
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
    read_output_file_mock.assert_called_once_with(output_file)
    get_rds_eol_data_mock.assert_has_calls(
        [
            mocker.call(Engine("postgres:https://example.com/postgres")),
            mocker.call(Engine("mysql:https://example.com/mysql")),
        ]
    )
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
