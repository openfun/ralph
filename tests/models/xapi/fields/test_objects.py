"""Tests for the xAPI object fields."""

from ralph.models.xapi.navigation.fields.objects import PageObjectField

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(PageObjectField)
def test_models_xapi_fields_object_page_object_field(field):
    """Tests that a page object field contains a definition with the expected values."""

    assert field.definition.type == "http://activitystrea.ms/schema/1.0/page"
    assert field.definition.name == {"en-US": "page"}
