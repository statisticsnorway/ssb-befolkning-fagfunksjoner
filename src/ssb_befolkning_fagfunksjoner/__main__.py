"""Command-line interface."""

import click


@click.command()
@click.version_option()
def main() -> None:
    """Befolkning Fagfunksjoner."""


if __name__ == "__main__":
    main(prog_name="ssb-befolkning-fagfunksjoner")  # pragma: no cover
