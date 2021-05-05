"""Common xAPI verb field definitions"""

from ..config import BaseModelWithConfig
from ..constants import EN, TERMINATED, VIEWED, XAPI_VERB_TERMINATED, XAPI_VERB_VIEWED


class PageViewedVerbField(BaseModelWithConfig):
    """Represents the `verb` xAPI Field for page viewed xAPI statement.

    Attributes:
       id (str): Consists of the value `http://id.tincanapi.com/verb/viewed`.
       display (dict): Consists of the dictionary `{"en": "viewed"}`.
    """

    id: XAPI_VERB_VIEWED = XAPI_VERB_VIEWED.__args__[0]
    display: dict[EN, VIEWED] = {EN.__args__[0]: VIEWED.__args__[0]}


class PageTerminatedVerbField(BaseModelWithConfig):
    """Represents the `verb` xAPI Field for page terminated xAPI statement.

    Attributes:
       id (str): Consists of the value `http://adlnet.gov/expapi/verbs/terminated`.
       display (dict): Consists of the dictionary `{"en": "terminated"}`.
    """

    id: XAPI_VERB_TERMINATED = XAPI_VERB_TERMINATED.__args__[0]
    display: dict[EN, TERMINATED] = {EN.__args__[0]: TERMINATED.__args__[0]}
