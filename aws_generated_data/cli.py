import logging
from typing import Annotated

import typer
from rich.logging import RichHandler

from .commands import msk_eol, rds_eol

app = typer.Typer()
app.add_typer(rds_eol.app, name="rds-eol", help="RDS End of Life related commands.")
app.add_typer(msk_eol.app, name="msk-eol", help="MSK End of Life related commands.")


@app.callback(no_args_is_help=True)
def main(*, debug: Annotated[bool, typer.Option(help="Enable debug")] = False) -> None:
    logging.basicConfig(
        level="DEBUG" if debug else "INFO",
        format="%(name)-20s: %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
