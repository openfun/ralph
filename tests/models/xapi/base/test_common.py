"""Tests for common xAPI fields."""

import pytest
from pydantic import BaseModel, ValidationError

from ralph.models.xapi.base.common import IRI, LanguageMap, LanguageTag


@pytest.mark.parametrize(
    "values",
    [
        ({"iri": "http://localhost/foo/bar"}),
        ({"iri": "http://www.greek-one-half-sign-alternate-form.org/\U00010176"}),
    ],
)
def test_models_xapi_base_common_field_iri_with_valid_data(values):
    """Test that a valid verb field does not raise a `ValidationError`."""

    class DummyIRIModel(BaseModel):
        """A dummy pydantic model with an IRI field."""

        iri: IRI

    try:
        DummyIRIModel(**values)
    except ValidationError as err:
        pytest.fail(f"Valid IRI should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "values",
    [
        {"iri": None},
        {"iri": {}},
        {"iri": ""},
        {"iri": "localhost/foo/bar"},
        {"iri": "http://foo/<bar>"},
    ],
)
def test_models_xapi_base_common_field_iri_with_invalid_data(values):
    """Test that an invalid verb field raises a `ValidationError`."""

    class DummyIRIModel(BaseModel):
        """A dummy pydantic model with an IRI field."""

        iri: IRI

    with pytest.raises(ValidationError, match="not a valid 'IRI'"):
        DummyIRIModel(**values)


@pytest.mark.parametrize(
    "values",
    [
        ({"tag": "en"}),
        ({"tag": "fr"}),
        ({"tag": "en-US"}),
    ],
)
def test_models_xapi_base_common_field_language_tag_with_valid_data(values):
    """Test that a valid verb field does not raise a `ValidationError`."""

    class DummyLanguageTagModel(BaseModel):
        """A dummy pydantic model with a LanguageTag field."""

        tag: LanguageTag

    try:
        DummyLanguageTagModel(**values)
    except ValidationError as err:
        pytest.fail(f"Valid IRI should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "values",
    [
        {"tag": None},
        {"tag": {}},
        {"tag": ""},
        {"tag": "en-US-en"},
    ],
)
def test_models_xapi_base_common_field_language_tag_with_invalid_data(values):
    """Test that an invalid verb field raises a `ValidationError`."""

    class DummyLanguageTagModel(BaseModel):
        """A dummy pydantic model with a LanguageTag field."""

        tag: LanguageTag

    with pytest.raises(TypeError, match="Invalid RFC 5646 Language tag"):
        DummyLanguageTagModel(**values)


@pytest.mark.parametrize("values", [({"map": {"en": "Hello"}})])
def test_models_xapi_base_common_field_language_map_with_valid_data(values):
    """Test that a valid verb field does not raise a `ValidationError`."""

    class DummyLanguageMapModel(BaseModel):
        """A dummy pydantic model with a LanguageTag field."""

        map: LanguageMap

    try:
        DummyLanguageMapModel(**values)
    except ValidationError as err:
        pytest.fail(f"Valid LanguageMap should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "values,exception,error",
    [
        ({"map": None}, ValidationError, "map\n  Input should be a valid dictionary"),
        (
            {"map": "en-US-en"},
            ValidationError,
            "map\n  Input should be a valid dictionary",
        ),
        ({"map": {"en-US-en": 1}}, TypeError, "Invalid RFC 5646 Language tag"),
        (
            {"map": {"en-US": []}},
            ValidationError,
            "en-US\n  Input should be a valid string",
        ),
    ],
)
def test_models_xapi_base_common_field_language_map_with_invalid_data(
    values, exception, error
):
    """Test that an invalid verb field raises a `ValidationError`."""

    class DummyLanguageTagModel(BaseModel):
        """A dummy pydantic model with a LanguageTag field."""

        map: LanguageMap

    with pytest.raises(exception, match=error):
        DummyLanguageTagModel(**values)
