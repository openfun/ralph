"""All tests relative to scopes and permissions."""

from uuid import uuid4

import pytest

from fastapi.testclient import TestClient

from ralph.api import app

from tests.fixtures.auth import create_user

client = TestClient(app)




@pytest.mark.parametrize("user_scopes,query_options,is_authorized", [
    (["statements/read/mine"], "", False),
    (["statements/read/mine"], "?mine=True", True),

    (["all"], "", True),
    (["all"], "?mine=True", True),
    (["all/read"], "", True),
    (["statements/read"], "", True),
    (["statements/read/mine", "statements/read"], "", True),
])
def test_api_statements_get_statements_scopes_mine(fs, user_scopes, query_options, is_authorized):
    """Test that users with scopes limited to `statements/read/mine` are forced 
    to use `mine` option in when querying `GET /statements`.
    """

    # Check for scope /statements/read/mine without `mine` option
    user = "ralph"
    pwd = "admin"
    
    auth_credentials =  create_user(fs, user, pwd, user_scopes)

    statement = {"place": "holder"}

    response = client.get(
        f"/xAPI/statements/{query_options}",
        headers={"Authorization": f"Basic {auth_credentials}"}
    )
    print('yolo')
    print(user_scopes)
    print(response.content)
    if is_authorized:
        assert response.status_code != 400
    else:
        assert response.status_code == 400
        # TODO: add assertion on message



@pytest.mark.parametrize("user_scopes,is_authorized", [
    (["statements/read/mine"], False),
    (["define"], False),
    (["profile/read"], False),
    (["statements/read"], False),
    (["all/read"], False),

    (["statements/write"], True),
    (["all"], True),
    (["profile/read", "all"], True),
])
def test_api_statements_put_statements_scopes(fs, user_scopes, is_authorized):
    """Test PUT statements response code with authorized and unauthorized scopes.
    
    NB: This test ONLY covers endpoint access control. It does NOT cover any type 
    of permissions as to the content that can be written.
    """

    user = "ralph"
    pwd = "admin"
    auth_credentials =  create_user(fs, user, pwd, user_scopes)

    statement = {"place": "holder"}

    response = client.put(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=statement,
    )
    
    if is_authorized:
        assert response.status_code != 401
    else:
        assert response.status_code == 401
        assert response.json() == {
            "detail": "User scopes do not allow access to the requested endpoint"
        }

@pytest.mark.parametrize("user_scopes,is_authorized", [
    (["statements/read/mine"], False),
    (["define"], False),
    (["profile/read"], False),
    (["statements/read"], False),
    (["all/read"], False),

    (["statements/write"], True),
    (["all"], True),
    (["profile/read", "all"], True),
])
def test_api_statements_post_statements_scopes(fs, user_scopes, is_authorized):
    """Test POST statements response code with authorized and unauthorized scopes.
    
    NB: This test ONLY covers endpoint access control. It does NOT cover any type 
    of permissions as to the content that can be written.
    """

    user = "ralph"
    pwd = "admin"
    auth_credentials =  create_user(fs, user, pwd, user_scopes)

    statement = {"place": "holder"}

    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=statement,
    )
    
    if is_authorized:
        assert response.status_code != 401
    else:
        assert response.status_code == 401
        assert response.json() == {
            "detail": "User scopes do not allow access to the requested endpoint"
        }


@pytest.mark.parametrize("user_scopes,is_authorized", [
    (["define"], False),
    (["profile/read"], False),
    (["statements/write"], False),

    (["statements/read/mine"], True),
    (["statements/read"], True),
    (["all/read"], True),
    (["all"], True),
    (["profile/read", "all"], True),
])
def test_api_statements_get_statements_scopes(fs, user_scopes, is_authorized):
    """Test GET statements response code with authorized and unauthorized scopes.
    """

    user = "ralph"
    pwd = "admin"
    auth_credentials =  create_user(fs, user, pwd, user_scopes)

    statement = {"place": "holder"}

    response = client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"}
    )
    
    if is_authorized:
        assert response.status_code != 401
    else:
        assert response.status_code == 401
        assert response.json() == {
            "detail": "User scopes do not allow access to the requested endpoint"
        }


