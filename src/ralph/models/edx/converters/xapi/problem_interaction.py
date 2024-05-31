"""Problem interaction event xAPI Converter."""

from ralph.models.converter import ConversionItem
from ralph.models.edx.problem_interaction.statements import ProblemCheck
from ralph.models.xapi.concepts.constants.cmi5_profile import (
    CONTEXT_EXTENSION_SESSION_ID,
)
from ralph.models.xapi.quiz.statements import AssessmentAnsweredQuestion

from .base import BaseXapiConverter


class ProblemCheckToAssessmentAnsweredQuestion(BaseXapiConverter):
    """Converts a common edX `problem_check` event to xAPI."""

    __src__ = ProblemCheck
    __dest__ = AssessmentAnsweredQuestion

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""
        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "object__id",
                    None,
                    lambda event: self.platform_url
                    + "/xblock/block-v1:"
                    + event["context"]["course_id"]
                    + event["event"]["problem_id"],
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_SESSION_ID,
                    "session",
                ),
                ConversionItem(
                    "context__contextActivites__definition__type", "context__referer"
                ),
                ConversionItem(
                    "result__success",
                    None,
                    lambda event: event["event"]["success"] == "correct",
                ),
                ConversionItem("result__score__max", "event__maxgrade"),
                ConversionItem("result__score__min", None, lambda _: 0),
                ConversionItem("result__score__raw", "event__grade"),
                ConversionItem(
                    "result__score__scaled",
                    None,
                    lambda event: event["event"]["grade"] / event["event"]["max_grade"],
                ),
                ConversionItem(
                    "object__definition__interactionType",
                    None,
                    self.map_interaction_type,
                ),
            },
        )

    @staticmethod
    def map_interaction_type(event: str):
        """Maps `response_type` from EdX logs to xAPI `interactionType` values.

        Returns a value of `interactionType`.
        """
        response_type = event["event"]["submission"][0]["response_type"]
        interaction_type = "other"

        if response_type in (
            "choiceresponse",
            "multiplechoiceresponse",
            "choicetextresponse",
            "optionresponse",
        ):
            interaction_type = "choice"
        if response_type == "truefalseresponse":
            interaction_type = "true-false"
        if response_type in ("numericalresponse", "formularesponse"):
            interaction_type = "numerical"
        if response_type == "stringresponse":
            interaction_type = "long-fill-in"
        if response_type == "imageresponse":
            interaction_type = "matching"

        return interaction_type
