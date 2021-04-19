"""Tests for the textbook interaction event models"""

import json
import re

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.textbook_interaction import (
    BookEventField,
    TextbookInteractionBaseEventField,
    TextbookPdfChapterNavigatedEventField,
    TextbookPdfDisplayScaledEventField,
    TextbookPdfOutlineToggledEventField,
    TextbookPdfPageNavigatedEventField,
    TextbookPdfPageScrolledEventField,
    TextbookPdfSearchCaseSensitivityToggledEventField,
    TextbookPdfSearchExecutedEventField,
    TextbookPdfSearchHighlightToggledEventField,
    TextbookPdfSearchNavigatedNextEventField,
    TextbookPdfThumbnailNavigatedEventField,
    TextbookPdfThumbnailsToggledEventField,
    TextbookPdfZoomButtonsChangedEventField,
    TextbookPdfZoomMenuChangedEventField,
    UIBook,
    UITextbookPdfChapterNavigated,
    UITextbookPdfDisplayScaled,
    UITextbookPdfOutlineToggled,
    UITextbookPdfPageNavigated,
    UITextbookPdfPageScrolled,
    UITextbookPdfSearchCaseSensitivityToggled,
    UITextbookPdfSearchExecuted,
    UITextbookPdfSearchHighlightToggled,
    UITextbookPdfSearchNavigatedNext,
    UITextbookPdfThumbnailNavigated,
    UITextbookPdfThumbnailsToggled,
    UITextbookPdfZoomButtonsChanged,
    UITextbookPdfZoomMenuChanged,
)
from ralph.models.selector import ModelSelector


@settings(max_examples=1)
@given(st.builds(TextbookInteractionBaseEventField))
def test_fields_edx_textbook_interaction_base_event_field_with_valid_content(event):
    """Tests that a valid TextbookInteractionBaseEventField field does not raise
    a ValidationError."""

    assert re.match(
        (r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"),
        event.chapter,
    )


@pytest.mark.parametrize(
    "chapter",
    (
        "block-v2:orgX=CS11+20_T1+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        "block-v1:orgX=CS1120_T1+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        "block-v1:orgX=CS11=20_T1+tipe@sequential+block@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        "block-v1:orgX=CS11+20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        "block-v1:orgX=CS11+20_T1+type@sequential+block@d0d4a647742943z3951b45d9db8a0ea1file.pdf",
        "block-v1:orgX=CS11+20_T1+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea13file.pdf",
        "block-v1:orgX=CS11+20_T1+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea1file",
        "block-v1:orgX=CS11+20_T1+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea1file.jpg",
    ),
)
@settings(max_examples=1)
@given(st.builds(TextbookInteractionBaseEventField))
def test_fields_edx_textbook_interaction_base_event_field_with_invalid_content(
    chapter, event
):
    """Tests that an invalid TextbookInteractionBaseEventField field does not raise
    a ValidationError."""

    invalid_event = json.loads(event.json())
    invalid_event["chapter"] = chapter

    with pytest.raises(ValidationError, match="chapter\n  string does not match regex"):
        TextbookInteractionBaseEventField(**invalid_event)


@settings(max_examples=1)
@given(st.builds(TextbookPdfChapterNavigatedEventField))
def test_fields_edx_textbook_pdf_chapter_navigated_event_field_with_valid_content(
    event,
):
    """Tests that a valid TextbookPdfChapterNavigatedEventField field does not raise
    a ValidationError."""

    assert re.match(
        (r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"),
        event.chapter,
    )


@pytest.mark.parametrize(
    "chapter",
    (
        "asset-v2:orgX=CS11+20_T1+type@asset+block@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        "asset-v1:orgX=CS1120_T1+type@asset+block@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        "asset-v1:orgX=CS11=20_T1+tipe@asset+block@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        "asset-v1:orgX=CS11+20_T1+",
        "type@assetblock@d0d4a647742943e3951b45d9db8a0ea1file.pdf",
        "asset-v1:orgX=CS11+20_T1+type@asset+block@d0d4a647742943z3951b45d9db8a0ea1file.pdf",
        "asset-v1:orgX=CS11+20_T1+type@asset+block@d0d4a647742943e3951b45d9db8a0ea13file.pdf",
        "asset-v1:orgX=CS11+20_T1+type@asset+block@d0d4a647742943e3951b45d9db8a0ea1file",
    ),
)
@settings(max_examples=1)
@given(st.builds(TextbookPdfChapterNavigatedEventField))
def test_fields_edx_textbook_pdf_chapter_navigated_event_field_with_invalid_content(
    chapter, event
):
    """Tests that an invalid TextbookPdfChapterNavigatedEventField field does not raise
    a ValidationError."""

    invalid_event = json.loads(event.json())
    invalid_event["chapter"] = chapter

    with pytest.raises(ValidationError, match="chapter\n  string does not match regex"):
        TextbookPdfChapterNavigatedEventField(**invalid_event)


@settings(max_examples=1)
@given(
    st.builds(
        UIBook,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(BookEventField),
    )
)
def test_models_edx_ui_book_with_valid_event(event):
    """Tests given a book event the get_model method should return UIBook model."""

    event = json.loads(event.json())
    assert ModelSelector(module="ralph.models.edx").get_model(event) is UIBook


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfThumbnailsToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfThumbnailsToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_thumbnails_toggled_selector_with_valid_event(event):
    """Tests given a textbook.pdf.thumbnails.toggled event
    the get_model method should return UITextbookPdfThumbnailsToggled model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfThumbnailsToggled
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfThumbnailNavigated,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfThumbnailNavigatedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_thumbnail_navigated_selector_with_valid_event(
    event,
):
    """Tests given a textbook.pdf.thumbnail.navigated event
    the get_model method should return UITextbookPdfThumbnailNavigated model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfThumbnailNavigated
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfOutlineToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfOutlineToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_outline_toggled_selector_with_valid_event(event):
    """Tests given a textbook.pdf.outline.toggled event
    the get_model method should return UITextbookPdfOutlineToggled model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfOutlineToggled
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfChapterNavigated,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfChapterNavigatedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_chapter_navigated_selector_with_valid_event(event):
    """Tests given a textbook.pdf.chapter.navigated event
    the get_model method should return UITextbookPdfChapterNavigated model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfChapterNavigated
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfPageNavigated,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfPageNavigatedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_page_navigated_selector_with_valid_event(event):
    """Tests given a textbook.pdf.page.navigated event
    the get_model method should return UITextbookPdfPageNavigated model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfPageNavigated
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfZoomButtonsChanged,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfZoomButtonsChangedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_zoom_buttons_changed_selector_with_valid_event(
    event,
):
    """Tests given a textbook.pdf.zoom.buttons.changed event
    the get_model method should return UITextbookPdfZoomButtonsChanged model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfZoomButtonsChanged
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfZoomMenuChanged,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfZoomMenuChangedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_zoom_menu_changed_selector_with_valid_event(event):
    """Tests given a textbook.pdf.zoom.menu.changed event
    the get_model method should return UITextbookPdfZoomMenuChanged model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfZoomMenuChanged
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfDisplayScaled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfDisplayScaledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_display_scaled_selector_with_valid_event(event):
    """Tests given a textbook.pdf.display.scaled event
    the get_model method should return UITextbookPdfDisplayScaled model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfDisplayScaled
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfPageScrolled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfPageScrolledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_page_scrolled_selector_with_valid_event(event):
    """Tests given a textbook.pdf.page.scrolled event
    the get_model method should return UITextbookPdfPageScrolled model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfPageScrolled
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfSearchExecuted,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfSearchExecutedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_search_executed_selector_with_valid_event(event):
    """Tests given a textbook.pdf.search.executed event
    the get_model method should return UITextbookPdfSearchExecuted model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfSearchExecuted
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfSearchNavigatedNext,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfSearchNavigatedNextEventField),
    )
)
def test_models_edx_ui_textbook_pdf_search_navigated_next_selector_with_valid_event(
    event,
):
    """Tests given a textbook.pdf.search.navigatednext event
    the get_model method should return UITextbookPdfSearchNavigatedNext model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfSearchNavigatedNext
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfSearchHighlightToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfSearchHighlightToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_search_highlight_toggled_selector_with_valid_event(
    event,
):
    """Tests given a textbook.pdf.search.highlight.toggled event
    the get_model method should return UITextbookPdfSearchHighlightToggled model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfSearchHighlightToggled
    )


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfSearchCaseSensitivityToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfSearchCaseSensitivityToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_search_case_sensitivity_toggled_selector_with_valid_event(
    event,
):
    """Tests given a textbook.pdf.searchcasesensitivity.toggled event
    the get_model method should return UITextbookPdfSearchCaseSensitivityToggled model."""

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UITextbookPdfSearchCaseSensitivityToggled
    )
