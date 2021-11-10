"""Tests for the textbook interaction event models"""

import json
import re

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.textbook_interaction.fields.events import (
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
)
from ralph.models.edx.textbook_interaction.statements import (
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
def test_fields_edx_textbook_interaction_base_event_field_with_valid_content(field):
    """Tests that a valid `TextbookInteractionBaseEventField` does not raise
    a `ValidationError`.
    """

    assert re.match(
        (r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"),
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
@settings(max_examples=1)
@given(st.builds(TextbookInteractionBaseEventField))
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


@settings(max_examples=1)
@given(st.builds(TextbookPdfChapterNavigatedEventField))
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
@settings(max_examples=1)
@given(st.builds(TextbookPdfChapterNavigatedEventField))
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


@settings(max_examples=1)
@given(
    st.builds(
        UIBook,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(BookEventField),
    )
)
def test_models_edx_ui_book_with_valid_statement(statement):
    """Tests that a `book` statement has the expected `event_type` and `name`."""

    assert statement.event_type == "book"
    assert statement.name == "book"


@settings(max_examples=1)
@given(
    st.builds(
        UIBook,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(BookEventField),
    )
)
def test_models_edx_ui_book_selector_with_valid_statement(statement):
    """Tests given a `book` statement the selector `get_model` method should return
    `UIBook` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is UIBook


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfThumbnailsToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfThumbnailsToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_thumbnails_toggled_with_valid_statement(statement):
    """Tests that a `textbook.pdf.thumbnails.toggled` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.thumbnails.toggled"
    assert statement.name == "textbook.pdf.thumbnails.toggled"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfThumbnailsToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfThumbnailsToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_thumbnails_toggled_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.thumbnails.toggled` event the selector `get_model`
    method should return `UITextbookPdfThumbnailsToggled` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_thumbnail_navigated_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.thumbnail.navigated` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.thumbnail.navigated"
    assert statement.name == "textbook.pdf.thumbnail.navigated"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfThumbnailNavigated,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfThumbnailNavigatedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_thumbnail_navigated_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.thumbnail.navigated` statement the selector
    `get_model` method should return `UITextbookPdfThumbnailNavigated` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_outline_toggled_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.outline.toggled` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.outline.toggled"
    assert statement.name == "textbook.pdf.outline.toggled"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfOutlineToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfOutlineToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_outline_toggled_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.outline.toggled` statement the selector `get_model`
    method should return `UITextbookPdfOutlineToggled` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_chapter_navigated_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.chapter.navigated` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.chapter.navigated"
    assert statement.name == "textbook.pdf.chapter.navigated"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfChapterNavigated,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfChapterNavigatedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_chapter_navigated_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.chapter.navigated` statement the selector `get_model`
    method should return `UITextbookPdfChapterNavigated` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_page_navigated_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.page.navigated` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.page.navigated"
    assert statement.name == "textbook.pdf.page.navigated"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfPageNavigated,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfPageNavigatedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_page_navigated_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.page.navigated` statement the selector `get_model`
    method should return `UITextbookPdfPageNavigated` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_zoom_buttons_changed_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.zoom.buttons.changed` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.zoom.buttons.changed"
    assert statement.name == "textbook.pdf.zoom.buttons.changed"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfZoomButtonsChanged,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfZoomButtonsChangedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_zoom_buttons_changed_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.zoom.buttons.changed` statement the selector
    `get_model` method should return `UITextbookPdfZoomButtonsChanged` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_zoom_menu_changed_with_valid_statement(statement):
    """Tests that a `textbook.pdf.zoom.menu.changed` has the expected `event_type` and
    `name`.
    """

    assert statement.event_type == "textbook.pdf.zoom.menu.changed"
    assert statement.name == "textbook.pdf.zoom.menu.changed"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfZoomMenuChanged,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfZoomMenuChangedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_zoom_menu_changed_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.zoom.menu.changed` statement the selector `get_model`
    method should return `UITextbookPdfZoomMenuChanged` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_display_scaled_with_valid_statement(statement):
    """Tests that a `textbook.pdf.display.scaled` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.display.scaled"
    assert statement.name == "textbook.pdf.display.scaled"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfDisplayScaled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfDisplayScaledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_display_scaled_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.display.scaled` statement the selector `get_model`
    method should return `UITextbookPdfDisplayScaled` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_page_scrolled_with_valid_statement(statement):
    """Tests that a `textbook.pdf.page.scrolled` statement has the expected `event_type`
    and `name`.
    """

    assert statement.event_type == "textbook.pdf.page.scrolled"
    assert statement.name == "textbook.pdf.page.scrolled"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfPageScrolled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfPageScrolledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_page_scrolled_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.page.scrolled` statement the selector `get_model`
    method should return `UITextbookPdfPageScrolled` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_search_executed_with_valid_statement(statement):
    """Tests that a `textbook.pdf.search.executed` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.search.executed"
    assert statement.name == "textbook.pdf.search.executed"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfSearchExecuted,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfSearchExecutedEventField),
    )
)
def test_models_edx_ui_textbook_pdf_search_executed_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.search.executed` statement the selector `get_model`
    method should return `UITextbookPdfSearchExecuted` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_search_navigated_next_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.search.navigatednext` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.search.navigatednext"
    assert statement.name == "textbook.pdf.search.navigatednext"


@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfSearchNavigatedNext,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfSearchNavigatedNextEventField),
    )
)
def test_models_edx_ui_textbook_pdf_search_navigated_next_selector_with_valid_statement(
    statement,
):
    """Tests given a `textbook.pdf.search.navigatednext` statement the selector
    `get_model` method should return `UITextbookPdfSearchNavigatedNext` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_textbook_pdf_search_highlight_toggled_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.search.highlight.toggled` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.search.highlight.toggled"
    assert statement.name == "textbook.pdf.search.highlight.toggled"


# pylint: disable=line-too-long
@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfSearchHighlightToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfSearchHighlightToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_search_highlight_toggled_selector_with_valid_statement(  # noqa
    statement,
):
    """Tests given a `textbook.pdf.search.highlight.toggled` statement the selector
    `get_model` method should return `UITextbookPdfSearchHighlightToggled` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is UITextbookPdfSearchHighlightToggled
    )


# pylint: disable=line-too-long
@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfSearchCaseSensitivityToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfSearchCaseSensitivityToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_search_case_sensitivity_toggled_with_valid_statement(  # noqa
    statement,
):
    """Tests that a `textbook.pdf.searchcasesensitivity.toggled` statement has the
    expected `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.searchcasesensitivity.toggled"
    assert statement.name == "textbook.pdf.searchcasesensitivity.toggled"


# pylint: disable=line-too-long
@settings(max_examples=1)
@given(
    st.builds(
        UITextbookPdfSearchCaseSensitivityToggled,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(TextbookPdfSearchCaseSensitivityToggledEventField),
    )
)
def test_models_edx_ui_textbook_pdf_search_case_sensitivity_toggled_selector_with_valid_statement(  # noqa
    statement,
):
    """Tests given a `textbook.pdf.searchcasesensitivity.toggled` statement the selector
    `get_model` method should return `UITextbookPdfSearchCaseSensitivityToggled` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is UITextbookPdfSearchCaseSensitivityToggled
    )
