"""Tests for common xAPI fields"""

import pytest
from pydantic import BaseModel, ValidationError

from ralph.models.xapi.fields.common import IRI, LanguageMap, LanguageTag


@pytest.mark.parametrize(
    "values",
    [
        ({"iri": "http://localhost/foo/bar"}),
        ({"iri": "http://www.greek-one-half-sign-alternate-form.org/\U00010176"}),
    ],
)
def test_models_xapi_fields_common_field_iri_with_valid_data(values):
    """Tests that a valid verb field does not raise a `ValidationError`."""

    class DummyIRIModel(BaseModel):
        """A dummy pydantic model with an IRI field."""

        iri: IRI

    try:
        DummyIRIModel(**values)
    except ValidationError as err:
        pytest.fail(f"Valid IRI should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "values,error",
    [
        ({"iri": None}, "none is not an allowed value"),
        ({"iri": {}}, "expected string"),
        ({"iri": ""}, "not a valid 'IRI'"),
        ({"iri": "localhost/foo/bar"}, "not a valid 'IRI'"),
        ({"iri": "http://foo/<bar>"}, "not a valid 'IRI'"),
    ],
)
def test_models_xapi_fields_common_field_iri_with_invalid_data(values, error):
    """Tests that an invalid verb field raises a `ValidationError`."""

    class DummyIRIModel(BaseModel):
        """A dummy pydantic model with an IRI field."""

        iri: IRI

    with pytest.raises(ValidationError, match=error):
        DummyIRIModel(**values)


@pytest.mark.parametrize(
    "values",
    [
        ({"tag": "en"}),
        ({"tag": "fr"}),
        ({"tag": "en-US"}),
    ],
)
def test_models_xapi_fields_common_field_language_tag_with_valid_data(values):
    """Tests that a valid verb field does not raise a `ValidationError`."""

    class DummyLanguageTagModel(BaseModel):
        """A dummy pydantic model with a LanguageTag field."""

        tag: LanguageTag

    try:
        DummyLanguageTagModel(**values)
    except ValidationError as err:
        pytest.fail(f"Valid IRI should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "values,error",
    [
        ({"tag": None}, "none is not an allowed value"),
        ({"tag": {}}, "unhashable type: 'dict'"),
        ({"tag": ""}, "Invalid RFC 5646 Language tag"),
        ({"tag": "en-US-en"}, "Invalid RFC 5646 Language tag"),
    ],
)
def test_models_xapi_fields_common_field_language_tag_with_invalid_data(values, error):
    """Tests that an invalid verb field raises a `ValidationError`."""

    class DummyLanguageTagModel(BaseModel):
        """A dummy pydantic model with a LanguageTag field."""

        tag: LanguageTag

    with pytest.raises(ValidationError, match=error):
        DummyLanguageTagModel(**values)


@pytest.mark.parametrize("values", [({"map": {"en": "Hello"}})])
def test_models_xapi_fields_common_field_language_map_with_valid_data(values):
    """Tests that a valid verb field does not raise a `ValidationError`."""

    class DummyLanguageMapModel(BaseModel):
        """A dummy pydantic model with a LanguageTag field."""

        map: LanguageMap

    try:
        DummyLanguageMapModel(**values)
    except ValidationError as err:
        pytest.fail(f"Valid LanguageMap should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "values,error",
    [
        ({"map": None}, "none is not an allowed value"),
        ({"map": "en-US-en"}, "value is not a valid dict"),
        ({"map": {"en-US-en": 1}}, "Invalid RFC 5646 Language tag"),
        ({"map": {"en-US": []}}, "en-US\n  str type expected"),
    ],
)
def test_models_xapi_fields_common_field_language_map_with_invalid_data(values, error):
    """Tests that an invalid verb field raises a `ValidationError`."""

    class DummyLanguageTagModel(BaseModel):
        """A dummy pydantic model with a LanguageTag field."""

        map: LanguageMap

    with pytest.raises(ValidationError, match=error):
        DummyLanguageTagModel(**values)
