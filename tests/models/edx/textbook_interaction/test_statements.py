"""Tests for the textbook interaction event models."""

import json

import pytest

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

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [
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
    ],
)
def test_models_edx_ui_textbook_interaction_selectors_with_valid_statements(class_):
    """Test given a valid textbook interaction edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_ui_book_with_valid_statement():
    """Test that a `book` statement has the expected `event_type` and `name`."""
    statement = mock_instance(UIBook)
    assert statement.event_type == "book"
    assert statement.name == "book"


def test_models_edx_ui_textbook_pdf_thumbnails_toggled_with_valid_statement():
    """Test that a `textbook.pdf.thumbnails.toggled` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfThumbnailsToggled)
    assert statement.event_type == "textbook.pdf.thumbnails.toggled"
    assert statement.name == "textbook.pdf.thumbnails.toggled"


def test_models_edx_ui_textbook_pdf_thumbnail_navigated_with_valid_statement():
    """Test that a `textbook.pdf.thumbnail.navigated` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfThumbnailNavigated)
    assert statement.event_type == "textbook.pdf.thumbnail.navigated"
    assert statement.name == "textbook.pdf.thumbnail.navigated"


def test_models_edx_ui_textbook_pdf_outline_toggled_with_valid_statement():
    """Test that a `textbook.pdf.outline.toggled` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfOutlineToggled)
    assert statement.event_type == "textbook.pdf.outline.toggled"
    assert statement.name == "textbook.pdf.outline.toggled"


def test_models_edx_ui_textbook_pdf_chapter_navigated_with_valid_statement():
    """Test that a `textbook.pdf.chapter.navigated` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfChapterNavigated)
    assert statement.event_type == "textbook.pdf.chapter.navigated"
    assert statement.name == "textbook.pdf.chapter.navigated"


def test_models_edx_ui_textbook_pdf_page_navigated_with_valid_statement():
    """Test that a `textbook.pdf.page.navigated` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfPageNavigated)
    assert statement.event_type == "textbook.pdf.page.navigated"
    assert statement.name == "textbook.pdf.page.navigated"


def test_models_edx_ui_textbook_pdf_zoom_buttons_changed_with_valid_statement():
    """Test that a `textbook.pdf.zoom.buttons.changed` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfZoomButtonsChanged)
    assert statement.event_type == "textbook.pdf.zoom.buttons.changed"
    assert statement.name == "textbook.pdf.zoom.buttons.changed"


def test_models_edx_ui_textbook_pdf_zoom_menu_changed_with_valid_statement():
    """Test that a `textbook.pdf.zoom.menu.changed` has the expected `event_type` and
    `name`.
    """
    statement = mock_instance(UITextbookPdfZoomMenuChanged)
    assert statement.event_type == "textbook.pdf.zoom.menu.changed"
    assert statement.name == "textbook.pdf.zoom.menu.changed"


def test_models_edx_ui_textbook_pdf_display_scaled_with_valid_statement():
    """Test that a `textbook.pdf.display.scaled` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfDisplayScaled)
    assert statement.event_type == "textbook.pdf.display.scaled"
    assert statement.name == "textbook.pdf.display.scaled"


def test_models_edx_ui_textbook_pdf_page_scrolled_with_valid_statement():
    """Test that a `textbook.pdf.page.scrolled` statement has the expected `event_type`
    and `name`.
    """
    statement = mock_instance(UITextbookPdfPageScrolled)
    assert statement.event_type == "textbook.pdf.page.scrolled"
    assert statement.name == "textbook.pdf.page.scrolled"


def test_models_edx_ui_textbook_pdf_search_executed_with_valid_statement():
    """Test that a `textbook.pdf.search.executed` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfSearchExecuted)
    assert statement.event_type == "textbook.pdf.search.executed"
    assert statement.name == "textbook.pdf.search.executed"


def test_models_edx_ui_textbook_pdf_search_navigated_next_with_valid_statement():
    """Test that a `textbook.pdf.search.navigatednext` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfSearchNavigatedNext)
    assert statement.event_type == "textbook.pdf.search.navigatednext"
    assert statement.name == "textbook.pdf.search.navigatednext"


def test_models_edx_ui_textbook_pdf_search_highlight_toggled_with_valid_statement():
    """Test that a `textbook.pdf.search.highlight.toggled` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfSearchHighlightToggled)
    assert statement.event_type == "textbook.pdf.search.highlight.toggled"
    assert statement.name == "textbook.pdf.search.highlight.toggled"


def test_models_edx_ui_textbook_pdf_search_case_sensitivity_toggled_with_valid_statement():  # noqa
    """Test that a `textbook.pdf.searchcasesensitivity.toggled` statement has the
    expected `event_type` and `name`.
    """
    statement = mock_instance(UITextbookPdfSearchCaseSensitivityToggled)
    assert statement.event_type == "textbook.pdf.searchcasesensitivity.toggled"
    assert statement.name == "textbook.pdf.searchcasesensitivity.toggled"
