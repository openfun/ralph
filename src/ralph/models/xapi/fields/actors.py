"""Common xAPI actor field definitions"""

from pydantic import AnyUrl

from ..config import BaseModelWithConfig


class ActorAccountField(BaseModelWithConfig):
    """Represents the `actor.account` xAPI field.

    Attributes:
        name (str): Consists of the unique id or name used to log in to this account.
        homePage (URL): Consists of the canonical home page for the system the account is on.
    """

    name: str
    homePage: AnyUrl  # URL < URI < IRI < String


class ActorField(BaseModelWithConfig):
    """Represents the `actor` xAPI Field.

    WARNING: It doesn't include the optional `objectType` and `name` fields.

    Attributes:
        account (ActorAccountField): See ActorAccountField.
    """

    account: ActorAccountField
