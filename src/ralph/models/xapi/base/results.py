"""Base xAPI `Result` definitions."""

from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Union

from pydantic import StrictBool, conint, root_validator

from ..config import BaseModelWithConfig
from .common import IRI

from ralph.conf import NonEmptyStrictStr


class BaseXapiResultScore(BaseModelWithConfig):
    """Pydantic model for result `score` property.

    Attributes:
        scaled (int): Consists of the normalized score related to the experience.
        raw (Decimal): Consists of the non-normalized score achieved by the Actor.
        min (Decimal): Consists of the lowest possible score.
        max (Decimal): Consists of the highest possible score.
    """

    scaled: Optional[conint(ge=-1, le=1)]
    raw: Optional[Decimal]
    min: Optional[Decimal]
    max: Optional[Decimal]

    @root_validator
    @classmethod
    def check_raw_min_max_relation(cls, values: Any) -> Any:
        """Check the relationship `min < raw < max`."""
        raw_value = values.get("raw", None)
        min_value = values.get("min", None)
        max_value = values.get("max", None)

        if min_value:
            if max_value and min_value > max_value:
                raise ValueError("min cannot be greater than max")
            if raw_value and min_value > raw_value:
                raise ValueError("min cannot be greater than raw")
        if max_value:
            if raw_value and raw_value > max_value:
                raise ValueError("raw cannot be greater than max")

        return values

from pydantic import Field
from typing import Annotated
class BaseXapiResult(BaseModelWithConfig):
    """Pydantic model for `result` property.

    Attributes:
        score (dict): See BaseXapiResultScore.
        success (bool): Indicates whether the attempt on the Activity was successful.
        completion (bool): Indicates whether the Activity was completed.
        response (str): Consists of the response for the given Activity.
        duration (timedelta): Consists of the duration over which the Statement
            occurred.
        extensions (dict): Consists of a dictionary of other properties as needed.
    """

    score: Optional[BaseXapiResultScore]
    success: Optional[StrictBool]
    completion: Optional[StrictBool]
    response: Optional[NonEmptyStrictStr]
    duration: Optional[timedelta]
    extensions: Optional[Dict[IRI, Union[str, int, bool, list, dict, None]]]
