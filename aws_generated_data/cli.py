import logging

import typer
from rich.logging import RichHandler

from .commands import rds_eol

app = typer.Typer()
app.add_typer(rds_eol.app, name="rds-eol", help="RDS End of Life related commands.")


@app.callback(no_args_is_help=True)
def main(debug: bool = typer.Option(False, help="Enable debug")) -> None:
    logging.basicConfig(
        level="DEBUG" if debug else "INFO",
        format="%(name)-20s: %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
