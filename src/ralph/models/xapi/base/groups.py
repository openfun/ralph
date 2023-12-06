"""Base xAPI `Group` definitions."""

import sys
from abc import ABC
from typing import List, Optional, Union

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
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

from ralph.conf import NonEmptyStrictStr


class BaseXapiGroupCommonProperties(BaseModelWithConfig, ABC):
    """Pydantic model for core `Group` type property.

    It is defined for the Group which performed the action.

    Attributes:
        objectType (str): Consists of the value `Group`.
        name (str): Consists of the full name of the Group.
    """

    objectType: Literal["Group"]
    name: Optional[NonEmptyStrictStr]


class BaseXapiAnonymousGroup(BaseXapiGroupCommonProperties):
    """Pydantic model for `Group` type property.

    It is defined for Anonymous Group type.

    Attributes:
        member (list): Consist of a list of the members of this Group.
    """

    member: List[BaseXapiAgent]


class BaseXapiIdentifiedGroup(BaseXapiGroupCommonProperties):
    """Pydantic model for `Group` type property.

    It is defined for Identified Group type.

    Attributes:
        member (list): Consist of a list of the members of this Group.
    """

    member: Optional[List[BaseXapiAgent]]


class BaseXapiIdentifiedGroupWithMbox(BaseXapiIdentifiedGroup, BaseXapiMboxIFI):
    """Pydantic model for `Group` type property.

    It is defined for group type with a mailto IFI.
    """


class BaseXapiIdentifiedGroupWithMboxSha1Sum(
    BaseXapiIdentifiedGroup, BaseXapiMboxSha1SumIFI
):
    """Pydantic model for `Group` type property.

    It is defined for group type with a hash IFI.
    """


class BaseXapiIdentifiedGroupWithOpenId(BaseXapiIdentifiedGroup, BaseXapiOpenIdIFI):
    """Pydantic model for `Group` type property.

    It is defined for group type with an openID IFI.
    """


class BaseXapiIdentifiedGroupWithAccount(BaseXapiIdentifiedGroup, BaseXapiAccountIFI):
    """Pydantic model for `Group` type property.

    It is defined for group type with an account IFI.
    """


BaseXapiGroup = Union[
    BaseXapiAnonymousGroup,
    BaseXapiIdentifiedGroupWithMbox,
    BaseXapiIdentifiedGroupWithMboxSha1Sum,
    BaseXapiIdentifiedGroupWithOpenId,
    BaseXapiIdentifiedGroupWithAccount,
]
