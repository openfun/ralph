"""Tests for the api.auth module."""

import pytest

from ralph.api.auth import ServerUsersCredentials, UserCredentials


def test_api_auth_model_serveruserscredentials():
    """Test api.auth ServerUsersCredentials model."""

    users = ServerUsersCredentials(
        __root__=[
            UserCredentials(
                username="johndoe",
                hash="notrealhash",
                scopes=["johndoe_scope"],
                agent={"mbox": "mailto:johndoe@example.com"},
            ),
            UserCredentials(
                username="foo",
                hash="notsorealhash",
                scopes=["foo_scope"],
                agent={"mbox": "mailto:foo@example.com"},
            ),
        ]
    )
    other_users = ServerUsersCredentials.parse_obj(
        [
            UserCredentials(
                username="janedoe",
                hash="notreallyrealhash",
                scopes=["janedoe_scope"],
                agent={"mbox": "mailto:janedoe@example.com"},
            ),
        ]
    )

    # Test addition operator
    users += other_users

    # Test len
    assert len(users) == 3

    # Test getitem
    assert users[0].username == "johndoe"
    assert users[1].username == "foo"
    assert users[2].username == "janedoe"

    # Test iterator
    usernames = [user.username for user in users]
    assert len(usernames) == 3
    assert usernames == ["johndoe", "foo", "janedoe"]

    # Test username uniqueness validator
    with pytest.raises(
        ValueError,
        match="You cannot create multiple credentials with the same username",
    ):
        users += ServerUsersCredentials.parse_obj(
            [
                UserCredentials(
                    username="foo",
                    hash="notsorealhash",
                    scopes=["foo_scope"],
                    agent={"mbox": "mailto:foo2@example.com"},
                ),
            ]
        )
