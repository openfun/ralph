"""Utilities for testing Ralph."""
import datetime
import hashlib
import uuid

from ralph.utils import statements_are_equivalent


def string_is_date(string: str):
    """Check if string can be parsed as a date."""
    try:
        datetime.datetime.fromisoformat(string)
        return True
    except ValueError:
        return False


def string_is_uuid(string: str):
    """Check if string is a valid uuid."""
    try:
        uuid.UUID(string)
        return True
    except ValueError:
        return False


def assert_statement_get_responses_are_equivalent(response_1: dict, response_2: dict):
    """Check that responses to GET /statements are equivalent.

    Check that all statements in response are equivalent, meaning that all
    fields not modified by the LRS are equal.
    """

    assert response_1.keys() == response_2.keys()

    def _all_but_statements(response):
        return {key: val for key, val in response.items() if key != "statements"}

    assert _all_but_statements(response_1) == _all_but_statements(response_2)

    # Assert the statements part of the response is equivalent
    assert "statements" in response_1.keys()
    assert "statements" in response_2.keys()
    assert len(response_1["statements"]) == len(response_2["statements"])

    for statement_1, statement_2 in zip(
        response_1["statements"], response_2["statements"]
    ):
        assert statements_are_equivalent(
            statement_1, statement_2
        ), "Statements in get responses are not equivalent, or not in the same order."


def create_mock_activity(id_: int = 0):
    """Create distinct activites with valid IRIs.

    args:
        id_: An integer used to uniquely identify the created agent.

    """
    return {
        "objectType": "Activity",
        "id": f"http://example.com/activity_{id_}",
    }


def create_mock_agent(
    ifi: str,
    id_: int,
    home_page_id=None,
    name: str = None,
    use_object_type: bool = True,
):
    """Create distinct mock agents with a given Inverse Functional Identifier.

    args:
        ifi: Inverse Functional Identifier. Possible values are:
            'mbox', 'mbox_sha1sum', 'openid' and 'account'.
        id_: An integer used to uniquely identify the created agent.
            If ifi=="account", agent equality requires same (id_, home_page_id)
        home_page (optional): The value of homePage, if ifi=="account"
        name (optional): name of the agent (NB: do not confuse with account.name
            with ifi=="account", or "username", as used in credentials)
    """
    agent = {}

    if use_object_type:
        agent["objectType"] = "Agent"

    if name is not None:
        agent["name"] = name

    # Add IFI fields
    if ifi == "mbox":
        agent["mbox"] = f"mailto:user_{id_}@testmail.com"
        return agent

    if ifi == "mbox_sha1sum":
        hash_object = hashlib.sha1(f"mailto:user_{id_}@testmail.com".encode("utf-8"))
        mail_hash = hash_object.hexdigest()
        agent["mbox_sha1sum"] = mail_hash
        return agent

    if ifi == "openid":
        agent["openid"] = f"http://user_{id_}.openid.exmpl.org"
        return agent

    if ifi == "account":
        if home_page_id is None:
            raise ValueError(
                "home_page_id must be defined if using create_mock_agent if "
                "using ifi=='account'"
            )
        agent["account"] = {
            "homePage": f"http://example_{home_page_id}.com",
            "name": f"username_{id_}",
        }
        return agent

    raise ValueError("No valid ifi was provided to create_mock_agent")
