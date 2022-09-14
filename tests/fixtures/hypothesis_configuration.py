"""Hypothesis fixture configuration."""

import operator

from hypothesis import provisional, settings
from hypothesis import strategies as st
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, Json, JsonWrapper, StrictStr
from pydantic._hypothesis_plugin import RESOLVERS, resolve_json

from ralph.models.xapi.fields.common import IRI, LanguageTag, MailtoEmail


def is_base_model(klass):
    """Return True if the given class is a subclass of the pydantic BaseModel."""
    try:
        return issubclass(klass, BaseModel)
    except TypeError:
        return False


def custom_resolve_json(cls):
    """Return a hypothesis build strategy for Json types."""
    if not is_base_model(getattr(cls, "inner_type", None)):
        return resolve_json(cls)
    return st.builds(cls.inner_type.json, st.from_type(cls.inner_type))


settings.register_profile("development", max_examples=1)
settings.load_profile("development")

st.register_type_strategy(str, st.text(min_size=1))
st.register_type_strategy(StrictStr, st.text(min_size=1))
st.register_type_strategy(AnyUrl, provisional.urls())
st.register_type_strategy(AnyHttpUrl, provisional.urls())
st.register_type_strategy(IRI, provisional.urls())
st.register_type_strategy(
    MailtoEmail, st.builds(operator.add, st.just("mailto:"), st.emails())
)
st.register_type_strategy(LanguageTag, st.just("en-US"))
st.register_type_strategy(Json, custom_resolve_json)
RESOLVERS[JsonWrapper] = custom_resolve_json
