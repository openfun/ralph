"""Constants for `Quiz` xAPI profile."""

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# Profile ID
PROFILE_ID_QUIZ = Literal["https://w3id.org/xapi/quiz"]  # pylint:disable=invalid-name
