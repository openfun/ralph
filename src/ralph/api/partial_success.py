"""Optional partial-success ingestion for POST /xAPI/statements.

See https://github.com/openfun/ralph/issues/622 — bulk backfill with a few
malformed events should not reject an entire batch when the client opts in via
``?partialSuccess=true`` (or ``?ignoreInvalid=true``).
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Tuple, Union

from fastapi import HTTPException, status
from pydantic import ValidationError

from ralph.api.models import LaxStatement, PartialSuccessError, PartialSuccessResponse


def partial_success_enabled(
    *,
    partial_success: Optional[bool],
    ignore_invalid: bool,
    default_enabled: bool = False,
) -> bool:
    """Return whether partial statement ingestion is active for this POST.

    Precedence: ``ignoreInvalid`` → explicit ``partialSuccess`` query param →
  server default (``RALPH_LRS_PARTIAL_SUCCESS_DEFAULT``).
    """
    if ignore_invalid:
        return True
    if partial_success is not None:
        return partial_success
    return default_enabled


def _validation_error_detail(
    exc: ValidationError, body_index: Optional[int]
) -> List[dict]:
    """Format pydantic errors like FastAPI (loc prefixed with body)."""
    detail: List[dict] = []
    for err in exc.errors():
        loc: Tuple[Union[str, int], ...] = ("body",)
        if body_index is not None:
            loc = ("body", body_index, *err.get("loc", ()))
        else:
            loc = ("body", *err.get("loc", ()))
        detail.append({**err, "loc": list(loc)})
    return detail


def _reason_from_validation_error(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "validation error"
    err = errors[0]
    loc = ".".join(str(part) for part in err.get("loc", ()) if part != "body")
    msg = err.get("msg", "validation error")
    if loc:
        return f"missing {loc}" if err.get("type") == "missing" else f"{loc}: {msg}"
    return str(msg)


def validate_strict_statements(body: Any) -> List[LaxStatement]:
    """Validate a POST body the same way as standard xAPI (all-or-nothing)."""
    if isinstance(body, list):
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The list of statements cannot be empty",
            )
        statements: List[LaxStatement] = []
        for index, item in enumerate(body):
            statements.append(_validate_one_statement(item, index))
        return statements

    return [_validate_one_statement(body, None)]


def _validate_one_statement(item: Any, index: Optional[int]) -> LaxStatement:
    if not isinstance(item, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "type": "model_attributes_type",
                    "loc": ["body"] if index is None else ["body", index],
                    "msg": "Input should be a valid dictionary or object to extract "
                    "fields from",
                    "input": item,
                }
            ],
        )
    try:
        return LaxStatement.model_validate(item)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_validation_error_detail(exc, index),
        ) from exc


def partition_statements(
    body: Any,
) -> Tuple[List[Tuple[int, LaxStatement]], List[PartialSuccessError]]:
    """Split a batch into valid statements and per-index rejection reasons."""
    if isinstance(body, list):
        items = list(enumerate(body))
    else:
        items = [(0, body)]

    valid: List[Tuple[int, LaxStatement]] = []
    errors: List[PartialSuccessError] = []
    seen_ids: dict[str, int] = {}

    for index, item in items:
        if not isinstance(item, dict):
            errors.append(
                PartialSuccessError(
                    index=index,
                    reason="input should be a valid dictionary or object",
                )
            )
            continue
        try:
            statement = LaxStatement.model_validate(item)
        except ValidationError as exc:
            errors.append(
                PartialSuccessError(
                    index=index,
                    reason=_reason_from_validation_error(exc),
                )
            )
            continue

        statement_id = str(statement.id) if statement.id is not None else None
        if statement_id is not None:
            if statement_id in seen_ids:
                errors.append(
                    PartialSuccessError(
                        index=index,
                        reason="duplicate statement ID in the list of statements",
                    )
                )
                continue
            seen_ids[statement_id] = index

        valid.append((index, statement))

    return valid, errors


def build_partial_success_response(
    *,
    inserted_ids: Sequence[str],
    errors: Sequence[PartialSuccessError],
) -> PartialSuccessResponse:
    """Build the partial-success JSON payload."""
    return PartialSuccessResponse(
        inserted=len(inserted_ids),
        rejected=len(errors),
        ids=list(inserted_ids),
        errors=list(errors),
    )
