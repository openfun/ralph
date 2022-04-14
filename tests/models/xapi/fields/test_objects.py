"""Tests for the xAPI object fields"""

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.xapi.navigation.fields.objects import PageObjectField


@settings(max_examples=1)
@given(st.builds(PageObjectField, id=provisional.urls()))
def test_models_xapi_fields_object_page_object_field(field):
    """Tests that a page object field contains a definition with the expected values."""

    assert field.definition.type == "http://activitystrea.ms/schema/1.0/page"
    assert field.definition.name == {"en-US": "page"}
