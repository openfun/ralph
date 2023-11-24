"""Hypothesis build strategies with special constraints."""

import random
from typing import Union

from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel

from ralph.models.edx.navigational.fields.events import NavigationalEventField
from ralph.models.edx.navigational.statements import UISeqNext, UISeqPrev
from ralph.models.xapi.base.contexts import BaseXapiContext
from ralph.models.xapi.base.results import BaseXapiResultScore
from ralph.models.xapi.lms.contexts import (
    LMSContextContextActivities,
    LMSProfileActivity,
)
from ralph.models.xapi.video.contexts import (
    VideoContextContextActivities,
    VideoProfileActivity,
)
from ralph.models.xapi.virtual_classroom.contexts import (
    VirtualClassroomContextContextActivities,
    VirtualClassroomProfileActivity,
)

OVERWRITTEN_STRATEGIES = {}


def is_base_model(klass):
    """Return True if the given class is a subclass of the pydantic BaseModel."""

    try:
        return issubclass(klass, BaseModel)
    except TypeError:
        return False


def get_strategy_from(annotation):
    """Infer a Hypothesis strategy from the given annotation."""
    origin = getattr(annotation, "__origin__", None)
    args = getattr(annotation, "__args__", None)
    if is_base_model(annotation):
        return custom_builds(annotation)
    if origin is Union:
        return st.one_of(
            [get_strategy_from(t) for t in args if not isinstance(t, type(None))]
        )
    if origin is list:
        return st.lists(get_strategy_from(args[0]), min_size=1)
    if origin is dict:
        keys = get_strategy_from(args[0])
        values = get_strategy_from(args[1])
        return st.dictionaries(keys, values, min_size=1)
    if annotation is None:
        return st.none()
    return st.from_type(annotation)


def custom_builds(
    klass: BaseModel, _overwrite_default=True, **kwargs: Union[st.SearchStrategy, bool]
):
    """Return a fixed_dictionaries Hypothesis strategy for pydantic models.

    Args:
        klass (BaseModel): The pydantic model for which to generate a strategy.
        _overwrite_default (bool): By default, fields overwritten by kwargs become
            required. If _overwrite_default is set to False, we keep the original field
            requirement (either required or optional).
        **kwargs (SearchStrategy or bool): If kwargs contain search strategies, they
            overwrite the default strategy for the given key.
            If kwargs contains booleans, they set whether the given key should be
            present (True) or omitted (False) in the generated model.
    """

    for special_class, special_kwargs in OVERWRITTEN_STRATEGIES.items():
        if issubclass(klass, special_class):
            kwargs = dict(special_kwargs, **kwargs)
            break
    optional = {}
    required = {}
    for name, field in klass.__fields__.items():
        arg = kwargs.get(name, None)
        if arg is False:
            continue
        is_required = field.required or (arg is not None and _overwrite_default)
        required_optional = required if is_required or arg is not None else optional
        field_strategy = get_strategy_from(field.outer_type_) if arg is None else arg
        required_optional[field.alias] = field_strategy
    if not required:
        # To avoid generating empty values
        key, value = random.choice(list(optional.items()))
        required[key] = value
        del optional[key]
    return st.fixed_dictionaries(required, optional=optional).map(klass.parse_obj)


def custom_given(*args: Union[st.SearchStrategy, BaseModel], **kwargs):
    """Wrap the Hypothesis `given` function. Replace st.builds with custom_builds."""
    strategies = []
    for arg in args:
        strategies.append(custom_builds(arg) if is_base_model(arg) else arg)
    return given(*strategies, **kwargs)

# from polyfactory.factories.pydantic_factory import ModelFactory

# def custom_given(klass):
#     def wrapper(func):
#         ModelFactor.create_factory(model=klass)
#         func()
#     return wrapper


OVERWRITTEN_STRATEGIES = {
    UISeqPrev: {
        "event": custom_builds(NavigationalEventField, old=st.just(1), new=st.just(0))
    },
    UISeqNext: {
        "event": custom_builds(NavigationalEventField, old=st.just(0), new=st.just(1))
    },
    BaseXapiContext: {
        "revision": False,
        "platform": False,
    },
    BaseXapiResultScore: {
        "raw": False,
        "min": False,
        "max": False,
    },
    LMSContextContextActivities: {"category": custom_builds(LMSProfileActivity)},
    VideoContextContextActivities: {"category": custom_builds(VideoProfileActivity)},
    VirtualClassroomContextContextActivities: {
        "category": custom_builds(VirtualClassroomProfileActivity)
    },
}
