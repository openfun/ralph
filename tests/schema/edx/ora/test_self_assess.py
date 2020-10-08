"""
Tests for the SelfAssess event schema
"""
from ralph.schemas.edx.ora.self_assess import SelfAssessSchema

from tests.schema.edx.test_common import check_loading_valid_events

def test_loading_valid_events_should_not_raise_exceptions():
    """check that loading valid events does not raise exceptions"""
    check_loading_valid_events(SelfAssessSchema(), "self_assess")