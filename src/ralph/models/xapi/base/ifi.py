"""Base xAPI `Inverse Functional Identifier` definitions."""

from pydantic import AnyUrl, StrictStr, constr

from ..config import BaseModelWithConfig
from .common import IRI, MailtoEmail

from ralph.conf import NonEmptyStrictStr


class BaseXapiAccount(BaseModelWithConfig):
    """Pydantic model for IFI `account` property.

    Attributes:
        homePage (IRI): Consists of the home page of the account's service provider.
        name (str): Consists of the unique id or name of the Actor's account.
    """

    homePage: IRI
    name: NonEmptyStrictStr

from typing import Annotated
from pydantic import Field

class BaseXapiMboxIFI(BaseModelWithConfig):
    """Pydantic model for mailto Inverse Functional Identifier.

    Attributes:
        mbox (MailtoEmail): Consists of the Agent's email address.
    """
    pattern = r'mailto:\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    mbox: Annotated[str, Field(regex=pattern)]#MailtoEmail


class BaseXapiMboxSha1SumIFI(BaseModelWithConfig):
    """Pydantic model for hash Inverse Functional Identifier.

    Attributes:
        mbox_sha1sum (str): Consists of the SHA1 hash of the Agent's email address.
    """

    mbox_sha1sum: constr(regex=r"^[0-9a-f]{40}$")


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
