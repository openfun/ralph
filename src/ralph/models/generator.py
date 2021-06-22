"""Model generator definition"""

import inspect
import string
from types import GenericAlias
from typing import Optional, Union, get_args, get_origin

import pytest
from hypothesis import provisional
from hypothesis import strategies as st
from pydantic import AnyUrl, BaseModel, HttpUrl

from ralph.defaults import MODEL_PATH_SEPARATOR
from ralph.models.edx.navigational import UISeqNext, UISeqPrev
from ralph.utils import set_dict_value_from_path


def hypothesis_model_factory(model, **user_options):
    """Generates an model instance using hypothesis."""

    options = {}
    # Defaults
    for name, field in model.__fields__.items():
        name = field.alias if field.has_alias else name
        if field.default is not None:
            options[name] = field.default
            continue
        if inspect.isclass(field.type_) and type(field.type_) is not GenericAlias:
            if issubclass(field.type_, BaseModel):
                options[name] = hypothesis_model_factory(field.type_).dict(by_alias=True)
            elif field.type_ is str and hasattr(model.Config, "min_anystr_length") and not field.default:
                options[name] = st.text(
                    string.ascii_letters, min_size=model.Config.min_anystr_length
                ).example()
            elif issubclass(field.type_, (AnyUrl, HttpUrl)):
                options[name] = provisional.urls().example()
        elif get_origin(field.type_) is Union:
            if not {AnyUrl, HttpUrl}.isdisjoint(set(get_args(field.type_))):
                options[name] = provisional.urls().example()
            else:
                for union_arg in get_args(field.type_):
                    if inspect.isclass(union_arg) and issubclass(union_arg, BaseModel):
                        options[name] = hypothesis_model_factory(union_arg).dict(by_alias=True)
                        break
    # Special case for UISeqNext and UISeqPrev
    if issubclass(model, (UISeqNext, UISeqPrev)):
        options["event"]["new"] = 1 if model is UISeqNext else 0
        options["event"]["old"] = 0 if model is UISeqNext else 1

    for path, value in user_options.items():
        set_dict_value_from_path(options, path.split(MODEL_PATH_SEPARATOR), value)

    for option in options:
        options[option] = st.just(options[option])

    return st.builds(model, **options).example()
