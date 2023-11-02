"""Base xAPI `Inverse Functional Identifier` definitions."""

from pydantic import AnyUrl, StrictStr, StringConstraints
from typing_extensions import Annotated

from ..config import BaseModelWithConfig
from .common import IRI, MailtoEmail


class BaseXapiAccount(BaseModelWithConfig):
    """Pydantic model for IFI `account` property.

    Attributes:
        homePage (IRI): Consists of the home page of the account's service provider.
        name (str): Consists of the unique id or name of the Actor's account.
    """

    homePage: IRI
    name: StrictStr


class BaseXapiMboxIFI(BaseModelWithConfig):
    """Pydantic model for mailto Inverse Functional Identifier.

    Attributes:
        mbox (MailtoEmail): Consists of the Agent's email address.
    """

    mbox: MailtoEmail


class BaseXapiMboxSha1SumIFI(BaseModelWithConfig):
    """Pydantic model for hash Inverse Functional Identifier.

    Attributes:
        mbox_sha1sum (str): Consists of the SHA1 hash of the Agent's email address.
    """

    mbox_sha1sum: Annotated[
        str, StringConstraints(pattern=r"^[0-9a-f]{40}$")
    ]  # noqa:F722


class BaseXapiOpenIdIFI(BaseModelWithConfig):
    """Pydantic model for OpenID Inverse Functional Identifier.

    Attributes:
        openid (URI): Consists of an openID that uniquely identifies the Agent.
    """

    openid: AnyUrl


class BaseXapiAccountIFI(BaseModelWithConfig):
    """Pydantic model for account Inverse Functional Identifier.

    Attributes:
        account (dict): See BaseXapiAccount.
    """

    account: BaseXapiAccount
