"""Tests for textbook interaction models event fields"""

import json
import re

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.textbook_interaction.fields.events import (
    TextbookInteractionBaseEventField,
    TextbookPdfChapterNavigatedEventField,
)

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(TextbookInteractionBaseEventField)
def test_fields_edx_textbook_interaction_base_event_field_with_valid_content(field):
    """Tests that a valid `TextbookInteractionBaseEventField` does not raise
    a `ValidationError`.
    """

    assert re.match(
        r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$",
        field.chapter,
    )


@pytest.mark.parametrize(
    "chapter",
    (
        (
            "block-v2:orgX=CS11+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1file.pdf"
        ),
        (
            "block-v1:orgX=CS1120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1file.pdf"
        ),
        (
            "block-v1:orgX=CS11=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1file.pdf"
        ),
        "block-v1:orgX=CS11+20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        (
            "block-v1:orgX=CS11+20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1file.pdf"
        ),
        (
            "block-v1:orgX=CS11+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13file.pdf"
        ),
        (
            "block-v1:orgX=CS11+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1file"
        ),
        (
            "block-v1:orgX=CS11+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1file.jpg"
        ),
    ),
)
@custom_given(TextbookInteractionBaseEventField)
def test_fields_edx_textbook_interaction_base_event_field_with_invalid_content(
    chapter, field
):
    """Tests that an invalid `TextbookInteractionBaseEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["chapter"] = chapter

    with pytest.raises(ValidationError, match="chapter\n  string does not match regex"):
        TextbookInteractionBaseEventField(**invalid_field)


@custom_given(TextbookPdfChapterNavigatedEventField)
def test_fields_edx_textbook_pdf_chapter_navigated_event_field_with_valid_content(
    field,
):
    """Tests that a valid `TextbookPdfChapterNavigatedEventField` does not raise a
    `ValidationError`.
    """

    assert re.match(
        (r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"),
        field.chapter,
    )


@pytest.mark.parametrize(
    "chapter",
    (
        (
            "asset-v2:orgX=CS11+20_T1+type@asset+"
            "block@d0d4a647742943e3951b45d9db8a0ea1file.pdf"
        ),
        (
            "asset-v1:orgX=CS1120_T1+type@asset+"
            "block@d0d4a647742943e3951b45d9db8a0ea1file.pdf"
        ),
        (
            "asset-v1:orgX=CS11=20_T1+tipe@asset+"
            "block@d0d4a647742943e3951b45d9db8a0ea1file.pdf"
        ),
        "asset-v1:orgX=CS11+20_T1+",
        "type@assetblock@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        (
            "asset-v1:orgX=CS11+20_T1+type@asset+"
            "block@d0d4a647742943z3951b45d9db8a0ea1file.pdf"
        ),
        (
            "asset-v1:orgX=CS11+20_T1+type@asset+"
            "block@d0d4a647742943e3951b45d9db8a0ea13file.pdf"
        ),
        (
            "asset-v1:orgX=CS11+20_T1+type@asset+"
            "block@d0d4a647742943e3951b45d9db8a0ea1file"
        ),
    ),
)
@custom_given(TextbookPdfChapterNavigatedEventField)
def test_fields_edx_textbook_pdf_chapter_navigated_event_field_with_invalid_content(
    chapter, field
):
    """Tests that an invalid `TextbookPdfChapterNavigatedEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["chapter"] = chapter

    with pytest.raises(ValidationError, match="chapter\n  string does not match regex"):
        TextbookPdfChapterNavigatedEventField(**invalid_field)
