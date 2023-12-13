"""Hypothesis fixture configuration."""


from hypothesis import provisional, settings
from hypothesis import strategies as st
from pydantic import AnyHttpUrl, AnyUrl, StrictStr

from ralph.models.xapi.base.common import IRI, LanguageTag

settings.register_profile("development", max_examples=1)
settings.load_profile("development")

# from ralph.conf import NonEmptyStr, NonEmptyStrictStr
# st.register_type_strategy(NonEmptyStr, st.text(min_size=1))
# st.register_type_strategy(NonEmptyStrictStr, st.text(min_size=1))

st.register_type_strategy(str, st.text(min_size=1))
st.register_type_strategy(StrictStr, st.text(min_size=1))
st.register_type_strategy(AnyUrl, provisional.urls())
st.register_type_strategy(AnyHttpUrl, provisional.urls())
st.register_type_strategy(IRI, provisional.urls())
# st.register_type_strategy(
#     MailtoEmail, st.builds(operator.add, st.just("mailto:"), st.emails())
# )
st.register_type_strategy(LanguageTag, st.just("en-US"))
