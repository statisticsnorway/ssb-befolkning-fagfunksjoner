import getpass
import logging
import random
import re
from pathlib import Path
from typing import Any
from typing import Self

from saspy import SASsession

AUTHKEY = "IOM_Prod_Grid1"
PATTERN = re.compile(r"{SAS004}[A-Z\d]+")
logger = logging.getLogger(__name__)


class ManagedSASsession(SASsession):
    """SASsession with dunder enter an exit methods.

    This allow us to use a SASsession in a with block to ensure that the session is closed,
    even if the programs fails.

    Example usage:
    with ManagedSASsession() as sas_session:
        sas_session.saslib("OUTLIB", path=write_dir)
        sas_session.df2sd(df, table=filename, libref="OUTLIB")
    """

    def __init__(self, *, password: str | None = None) -> None:
        """Initialise ManagedSASsession class."""
        user_initials = getpass.getuser()
        server = _get_server_url()

        args = {
            "omruser": user_initials,
            "java": "/usr/bin/java",
            "iomhost": server,
            "iomport": 8591,
        }

        if password:
            args["omrpw"] = password
        else:
            args["authkey"] = AUTHKEY

        super().__init__(**args)

    def __enter__(self) -> Self:
        """Open SAS session."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Close SAS session."""
        self.endsas()


def _get_server_url() -> str:
    """Picks a SAS server at random."""
    server_nums = range(1, 1 + 6)
    random_num = random.choice(server_nums)
    sas_server = f"sl-sas-comp-p{random_num}.ssb.no"
    logger.info(f"Using SAS server: {sas_server}")
    return sas_server


def set_password() -> None:
    """Sets SAS-encoded password so that interacting with saspy does not prompt for a password every time."""
    user_initials = getpass.getuser()
    password = getpass.getpass("Passord:")

    with ManagedSASsession(password=password) as session:

        log = session.submit(f"""
        proc pwencode in='{password}' method=sas004;
        run;
        """)["LOG"]

    match = PATTERN.search(log)

    if not match:
        raise ValueError("Could not find SAS-encoded password.")

    token = match[0]

    authstring = f"{AUTHKEY} user {user_initials} password {token}"
    authfile_path = Path.home() / ".authinfo"

    if authfile_path.exists():
        with authfile_path.open("r+") as file:
            lines = file.read().splitlines()
            lines = filter(lambda x: not x.startswith(AUTHKEY), lines)
            file.seek(0)
            file.truncate()
            file.write("\n".join(lines))

            file.write(authstring)
    else:
        authfile_path.write_text(authstring)


# TODO: 
# 1. Er 'encodinga' sikker i en offentlig pakke?
# 2. mypy klager og manglende stubs
