"""Cohort event field definition."""

from ...base import AbstractBaseEventField


class CohortBaseEventField(AbstractBaseEventField):
    """Pydantic model for cohort core `event` field.

    Attributes:
        cohort_id (int): Consists of the numeric ID of the cohort.
        name (str): Consists of the display name of the cohort
    """

    cohort_id: int
    name: str


class CohortUserBaseEventField(CohortBaseEventField):
    """Pydantic model for cohort user core `event` field.

    Attributes:
        user_id (int): Consists of the numeric ID of the user.
    """

    user_id: int
