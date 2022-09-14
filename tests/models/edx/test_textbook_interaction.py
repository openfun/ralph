"""Tests for the textbook interaction event models."""

import json
import re

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.textbook_interaction.fields.events import (
    TextbookInteractionBaseEventField,
    TextbookPdfChapterNavigatedEventField,
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

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(TextbookInteractionBaseEventField)
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


@custom_given(UIBook)
def test_models_edx_ui_book_with_valid_statement(statement):
    """Tests that a `book` statement has the expected `event_type` and `name`."""

    assert statement.event_type == "book"
    assert statement.name == "book"


@custom_given(UIBook)
def test_models_edx_ui_book_selector_with_valid_statement(statement):
    """Tests given a `book` statement the selector `get_model` method should return
    `UIBook` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is UIBook


@custom_given(UITextbookPdfThumbnailsToggled)
def test_models_edx_ui_textbook_pdf_thumbnails_toggled_with_valid_statement(statement):
    """Tests that a `textbook.pdf.thumbnails.toggled` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.thumbnails.toggled"
    assert statement.name == "textbook.pdf.thumbnails.toggled"


@custom_given(UITextbookPdfThumbnailsToggled)
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


@custom_given(UITextbookPdfThumbnailNavigated)
def test_models_edx_ui_textbook_pdf_thumbnail_navigated_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.thumbnail.navigated` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.thumbnail.navigated"
    assert statement.name == "textbook.pdf.thumbnail.navigated"


@custom_given(UITextbookPdfThumbnailNavigated)
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


@custom_given(UITextbookPdfOutlineToggled)
def test_models_edx_ui_textbook_pdf_outline_toggled_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.outline.toggled` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.outline.toggled"
    assert statement.name == "textbook.pdf.outline.toggled"


@custom_given(UITextbookPdfOutlineToggled)
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


@custom_given(UITextbookPdfChapterNavigated)
def test_models_edx_ui_textbook_pdf_chapter_navigated_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.chapter.navigated` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.chapter.navigated"
    assert statement.name == "textbook.pdf.chapter.navigated"


@custom_given(UITextbookPdfChapterNavigated)
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


@custom_given(UITextbookPdfPageNavigated)
def test_models_edx_ui_textbook_pdf_page_navigated_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.page.navigated` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.page.navigated"
    assert statement.name == "textbook.pdf.page.navigated"


@custom_given(UITextbookPdfPageNavigated)
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


@custom_given(UITextbookPdfZoomButtonsChanged)
def test_models_edx_ui_textbook_pdf_zoom_buttons_changed_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.zoom.buttons.changed` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.zoom.buttons.changed"
    assert statement.name == "textbook.pdf.zoom.buttons.changed"


@custom_given(UITextbookPdfZoomButtonsChanged)
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


@custom_given(UITextbookPdfZoomMenuChanged)
def test_models_edx_ui_textbook_pdf_zoom_menu_changed_with_valid_statement(statement):
    """Tests that a `textbook.pdf.zoom.menu.changed` has the expected `event_type` and
    `name`.
    """

    assert statement.event_type == "textbook.pdf.zoom.menu.changed"
    assert statement.name == "textbook.pdf.zoom.menu.changed"


@custom_given(UITextbookPdfZoomMenuChanged)
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


@custom_given(UITextbookPdfDisplayScaled)
def test_models_edx_ui_textbook_pdf_display_scaled_with_valid_statement(statement):
    """Tests that a `textbook.pdf.display.scaled` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.display.scaled"
    assert statement.name == "textbook.pdf.display.scaled"


@custom_given(UITextbookPdfDisplayScaled)
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


@custom_given(UITextbookPdfPageScrolled)
def test_models_edx_ui_textbook_pdf_page_scrolled_with_valid_statement(statement):
    """Tests that a `textbook.pdf.page.scrolled` statement has the expected `event_type`
    and `name`.
    """

    assert statement.event_type == "textbook.pdf.page.scrolled"
    assert statement.name == "textbook.pdf.page.scrolled"


@custom_given(UITextbookPdfPageScrolled)
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


@custom_given(UITextbookPdfSearchExecuted)
def test_models_edx_ui_textbook_pdf_search_executed_with_valid_statement(statement):
    """Tests that a `textbook.pdf.search.executed` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.search.executed"
    assert statement.name == "textbook.pdf.search.executed"


@custom_given(UITextbookPdfSearchExecuted)
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


@custom_given(UITextbookPdfSearchNavigatedNext)
def test_models_edx_ui_textbook_pdf_search_navigated_next_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.search.navigatednext` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.search.navigatednext"
    assert statement.name == "textbook.pdf.search.navigatednext"


@custom_given(UITextbookPdfSearchNavigatedNext)
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


@custom_given(UITextbookPdfSearchHighlightToggled)
def test_models_edx_ui_textbook_pdf_search_highlight_toggled_with_valid_statement(
    statement,
):
    """Tests that a `textbook.pdf.search.highlight.toggled` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.search.highlight.toggled"
    assert statement.name == "textbook.pdf.search.highlight.toggled"


# pylint: disable=line-too-long
@custom_given(UITextbookPdfSearchHighlightToggled)
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
@custom_given(UITextbookPdfSearchCaseSensitivityToggled)
def test_models_edx_ui_textbook_pdf_search_case_sensitivity_toggled_with_valid_statement(  # noqa
    statement,
):
    """Tests that a `textbook.pdf.searchcasesensitivity.toggled` statement has the
    expected `event_type` and `name`.
    """

    assert statement.event_type == "textbook.pdf.searchcasesensitivity.toggled"
    assert statement.name == "textbook.pdf.searchcasesensitivity.toggled"


# pylint: disable=line-too-long
@custom_given(UITextbookPdfSearchCaseSensitivityToggled)
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
