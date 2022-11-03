"""Common xAPI actor field definitions."""

from typing import Literal, Optional, Union

from pydantic import AnyUrl, StrictStr, constr

from ..config import BaseModelWithConfig
from .common import IRI, MailtoEmail


class AccountActorAccountField(BaseModelWithConfig):
    """Pydantic model for `actor.account` field.

    Attributes:
        homePage (IRI): Consists of the home page of the account's service provider.
        name (str): Consists of the unique id or name of the Actor's account.
    """

    homePage: IRI
    name: StrictStr


class BaseActorField(BaseModelWithConfig):
    """Pydantic model for core `actor` field.

    It defines who performed the action.

    Attributes:
        objectType (str): Consists of the value `Agent`.
        name (str): Consists of the full name of the Agent.
    """

    objectType: Optional[Literal["Agent"]]
    name: Optional[StrictStr]


class MboxActorField(BaseActorField):
    """Pydantic model for `actor` field.

    It defines a mailto Inverse Functional Identifier.

    Attributes:
        mbox (MailtoEmail): Consists of the Agent's email address.
    """

    mbox: MailtoEmail


class MboxSha1SumActorField(BaseActorField):
    """Pydantic model for `actor` field.

    It defines a hash Inverse Functional Identifier.

    Attributes:
        mbox_sha1sum (str): Consists of the SHA1 hash of the Agent's email address.
    """

    mbox_sha1sum: constr(regex=r"^[0-9a-f]{40}$")  # noqa:F722


class OpenIdActorField(BaseActorField):
    """Pydantic model for `actor` field.

    It defines an OpenID Inverse Functional Identifier.

    Attributes:
        openid (URI): Consists of an openID that uniquely identifies the Agent.
    """

    openid: AnyUrl


class AccountActorField(BaseActorField):
    """Pydantic model for `actor` field.

    It defines an account Inverse Functional Identifier.

    Attributes:
        account (dict): See AccountActorAccountField.
    """

    account: AccountActorAccountField


AgentActorField = Union[
    MboxActorField, MboxSha1SumActorField, OpenIdActorField, AccountActorField
]


class AnonymousGroupActorField(BaseActorField):
    """Pydantic model for `actor` field.

    It is defined for Anonymous Group type.

    Attributes:
        objectType (str): Consists of the value `Group`.
        member (list): Consist of a list of the members of this Group.
    """

    objectType: Literal["Group"]
    member: list[AgentActorField]


class BaseIdentifiedGroupActorField(AnonymousGroupActorField):
    """Pydantic model for `actor` field.

    It is defined for Identified Group type.

    Attributes:
        member (list): Consist of a list of the members of this Group.
    """

    member: Optional[list[AgentActorField]]


class MboxGroupActorField(BaseIdentifiedGroupActorField, MboxActorField):
    """Pydantic model for `actor` field.

    It is defined for group type with a mailto IFI.
    """


class MboxSha1SumGroupActorField(BaseIdentifiedGroupActorField, MboxSha1SumActorField):
    """Pydantic model for `actor` field.

    It is defined for group type with a hash IFI.
    """


class OpenIdGroupActorField(BaseIdentifiedGroupActorField, OpenIdActorField):
    """Pydantic model for `actor` field.

    It is defined for group type with an openID IFI.
    """


class AccountGroupActorField(BaseIdentifiedGroupActorField, AccountActorField):
    """Pydantic model for `actor` field.

    It is defined for group type with an account IFI.
    """


GroupActorField = Union[
    AnonymousGroupActorField,
    MboxGroupActorField,
    MboxSha1SumGroupActorField,
    OpenIdGroupActorField,
    AccountGroupActorField,
]
ActorField = Union[AgentActorField, GroupActorField]
