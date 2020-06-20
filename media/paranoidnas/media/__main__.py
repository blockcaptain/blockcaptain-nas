from pathlib import Path
from rich.logging import RichHandler
from rich.emoji import Emoji
from rich.console import Console
import logging
from isomodder import IsoModderFatalException
from typing import Any
import sys
import click
from ._media import create_paranoidnas_iso, create_paranoidnas_autoinstall_yaml, BootMode


MIN_PYTHON = (3, 6)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON)

console = Console()

logging.basicConfig(level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])


class EnumChoice(click.Choice):
    def __init__(self, enum, case_sensitive=False, use_value=False):
        self.enum = enum
        self.use_value = use_value
        choices = [str(e.value) if use_value else e.name for e in self.enum]
        super().__init__(choices, case_sensitive)

    def convert(self, value, param, ctx):
        try:
            return self.enum[value]
        except KeyError:
            pass

        result = super().convert(value, param, ctx)
        # Find the original case in the enum
        if not self.case_sensitive and result not in self.choices:
            result = next(c for c in self.choices if result.lower() == c.lower())
        if self.use_value:
            return next(e for e in self.enum if str(e.value) == result)
        return self.enum[result]


@click.group()
def cli():
    pass


def attach_autoinstall_options(function: Any) -> Any:
    click.option("-u", "--username", default="paranoid")(function)
    click.option("-h", "--hostname", default="paranoid")(function)
    click.option("-a", "--authorized-key", "authorized_keys", multiple=True)(function)
    click.option("-l", "--locale", default="en_US.UTF-8")(function)
    click.option("-k", "--kb-layout", default="us")(function)
    click.option(
        "-b", "--boot", "boot_mode", type=EnumChoice(BootMode, case_sensitive=False), default="EFI"
    )(function)
    return function


@cli.command()
@attach_autoinstall_options
@click.option("--prompt/--no-prompt", default=False)
def build(**kwargs):
    working_dir = Path("build")
    autoinstall_config = dict(kwargs)
    del autoinstall_config["prompt"]
    autoinstall_yaml = create_paranoidnas_autoinstall_yaml(**autoinstall_config)
    create_paranoidnas_iso(
        working_dir, kwargs["boot_mode"], autoinstall_yaml, autoinstall_prompt=kwargs["prompt"]
    )
    logging.info(f"You're ready to burn! {Emoji('fire')}")

    # print out info here


@cli.command()
@attach_autoinstall_options
def dumpautoinstall(**kwargs):
    autoinstall_yaml = create_paranoidnas_autoinstall_yaml(**kwargs)
    print(autoinstall_yaml)


def main():
    try:
        cli()
    except SystemExit:
        pass
    except IsoModderFatalException as exc:
        console.print()
        console.print(f":cross_mark: [bold red] {exc} :cross_mark:")
        console.print()
    except BaseException as exc:
        console.print()
        console.print(
            f":pile_of_poo: :whale: [bold red] Something totally unexpected has happened. Let's see..."
        )
        console.print()
        console.print_exception()
        console.print()


if __name__ == "__main__":
    main()
