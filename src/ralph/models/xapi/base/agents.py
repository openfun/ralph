"""Base xAPI `Agent` definitions."""

import sys
from abc import ABC
from typing import Optional, Union

from pydantic import StrictStr

from ..config import BaseModelWithConfig
from .common import IRI
from .ifi import (
    BaseXapiAccountIFI,
    BaseXapiMboxIFI,
    BaseXapiMboxSha1SumIFI,
    BaseXapiOpenIdIFI,
)

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class BaseXapiAgentAccount(BaseModelWithConfig):
    """Pydantic model for `Agent` type `account` property.

    Attributes:
        homePage (IRI): Consists of the home page of the account's service provider.
        name (str): Consists of the unique id or name of the Actor's account.
    """

    homePage: IRI
    name: StrictStr


class BaseXapiAgentCommonProperties(BaseModelWithConfig, ABC):
    """Pydantic model for core `Agent` type property.

    It defines who performed the action.

    Attributes:
        objectType (str): Consists of the value `Agent`.
        name (str): Consists of the full name of the Agent.
    """

    objectType: Optional[Literal["Agent"]]
    name: Optional[StrictStr]


class BaseXapiAgentWithMbox(BaseXapiAgentCommonProperties, BaseXapiMboxIFI):
    """Pydantic model for `Agent` type property.

    It is defined for agent type with a mailto IFI.
    """


class BaseXapiAgentWithMboxSha1Sum(
    BaseXapiAgentCommonProperties, BaseXapiMboxSha1SumIFI
):
    """Pydantic model for `Agent` type property.

    It is defined for agent type with a hash IFI.
    """


class BaseXapiAgentWithOpenId(BaseXapiAgentCommonProperties, BaseXapiOpenIdIFI):
    """Pydantic model for `Agent` type property.

    It is defined for agent type with an openID IFI.
    """


class BaseXapiAgentWithAccount(BaseXapiAgentCommonProperties, BaseXapiAccountIFI):
    """Pydantic model for `Agent` type property.

    It is defined for agent type with an account IFI.
    """


BaseXapiAgent = Union[
    BaseXapiAgentWithMbox,
    BaseXapiAgentWithMboxSha1Sum,
    BaseXapiAgentWithOpenId,
    BaseXapiAgentWithAccount,
]
