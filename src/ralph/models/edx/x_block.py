"""Base XBlock event model definition"""

from typing import Literal

from pydantic import constr

from ralph.models.edx.base import BaseContextField, BaseModelWithConfig
from ralph.models.edx.server import BaseServerEvent


class ContextModuleField(BaseModelWithConfig):
    """Represents the context `module` field.

    Attributes:
        usage_key (str): Consists of a block ID of the current component.
        display_name (str): Consists of a short description or title of the component.
    """

    usage_key: constr(regex=r"^block-v1:.+\+.+\+.+type@.+@[a-f0-9]{32}$")  # noqa:F722
    display_name: str


class ContextField(BaseContextField):
    """Represents the context field.

    Attributes:
        module (dict): see ContextModuleField.
    """

    module: ContextModuleField


class BaseXBlockEvent(BaseServerEvent):
    """Represents the base event model all events issued from XBlocks inherit from.

    Attributes:
        context (str): See ContextField.
        username (str): Consists of the unique username identifying the logged in user.
        page (str): Consists of the value `x_module`.
    """

    context: ContextField
    username: constr(min_length=2, max_length=30)
    page: Literal["x_module"]
