import re

from ssb_befolkning_fagfunksjoner.sas.sas_session import _get_server_url

def test_get_server_url() -> None:
    url = _get_server_url()
    assert re.match(r"sl-sas-comp-p[1-6]\.ssb\.no", url)
