"""Common xAPI actor field definitions"""

from typing import Literal, Optional

from pydantic import AnyUrl

from ..config import BaseModelWithConfig


class ActorAccountField(BaseModelWithConfig):
    """Represents the `actor.account` xAPI field.

    Attributes:
        name (str): Consists of the unique id or name used to log in to this account.
        homePage (URL): Consists of the canonical home page for the system the account
            is on.
    """

    name: str
    homePage: AnyUrl  # URL < URI < IRI < String


class ActorField(BaseModelWithConfig):
    """Represents the `actor` xAPI Field.

    Attributes:
        account (dict): See ActorAccountField.
        name (str): Consists of the full name of the Agent.
        objectType (str): Consists of the value `Agent`.
    """

    name: Optional[str]
    objectType: Optional[Literal["Agent"]]
    account: ActorAccountField
