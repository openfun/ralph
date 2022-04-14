"""Hypothesis fixture configuration"""

from hypothesis import provisional, settings
from hypothesis import strategies as st
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, Json, JsonWrapper
from pydantic._hypothesis_plugin import RESOLVERS, resolve_json


def is_base_model(klass):
    """Returns True if the given class is a subclass of the pydantic BaseModel."""

    try:
        return issubclass(klass, BaseModel)
    except TypeError:
        return False


def custom_resolve_json(cls):
    """Returns a hypothesis build strategy for Json types."""

    if not is_base_model(getattr(cls, "inner_type", None)):
        return resolve_json(cls)
    return st.builds(cls.inner_type.json, st.from_type(cls.inner_type))


settings.register_profile("development", max_examples=1)
settings.load_profile("development")

st.register_type_strategy(str, st.text(min_size=1))
st.register_type_strategy(AnyUrl, provisional.urls())
st.register_type_strategy(AnyHttpUrl, provisional.urls())
st.register_type_strategy(Json, custom_resolve_json)
RESOLVERS[JsonWrapper] = custom_resolve_json
