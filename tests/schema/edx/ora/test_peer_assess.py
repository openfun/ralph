"""
Tests for the PeerAssess event schema
"""
from ralph.schemas.edx.ora.peer_assess import PeerAssessSchema

from tests.schema.edx.test_common import check_loading_valid_events

def test_loading_valid_events_should_not_raise_exceptions():
    """check that loading valid events does not raise exceptions"""
    check_loading_valid_events(PeerAssessSchema(), "peer_assess")