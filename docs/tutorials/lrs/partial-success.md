# Partial success on bulk POST (issue #622)

By default, `POST /xAPI/statements` is **atomic**: if one statement in the batch
fails validation, the entire request is rejected (HTTP `400` / `422`) and **no**
statement from the batch is stored.

For large historical backfills (e.g. Open edX tracking logs → ClickHouse / ES),
losing a 10 000-statement batch because of a single malformed event is costly.
Ralph therefore supports an **opt-in** query flag:

- `?partialSuccess=true`
- `?ignoreInvalid=true` (alias)

Or set the server default (no query flag required on clients such as Moodle logstore):

```bash
RALPH_LRS_PARTIAL_SUCCESS_DEFAULT=true
```

Clients can still force xAPI-strict with `?partialSuccess=false` when the server default is on.

## Behaviour

| Mode | Invalid statement in batch | HTTP | Body |
|------|---------------------------|------|------|
| Default (xAPI-strict) | Any | `400` / `422` | Error detail — **nothing stored** |
| `partialSuccess=true` | Some | `200` | Report with `inserted`, `rejected`, `ids`, `errors` |
| `partialSuccess=true` | All | `400` | Report with `inserted: 0` |

### Example

```bash
curl -u ralph:secret \
  -X POST 'http://localhost:8100/xAPI/statements?partialSuccess=true' \
  -H 'Content-Type: application/json' \
  -H 'X-Experience-API-Version: 1.0.3' \
  -d '[
    {"actor":{"mbox":"mailto:a@example.com","objectType":"Agent"},"verb":{"id":"http://adlnet.gov/expapi/verbs/experienced"},"object":{"id":"https://example.com/1"}},
    {"bad":"event"},
    {"actor":{"mbox":"mailto:b@example.com","objectType":"Agent"},"verb":{"id":"http://adlnet.gov/expapi/verbs/experienced"},"object":{"id":"https://example.com/2"}}
  ]'
```

Response (`200`):

```json
{
  "inserted": 2,
  "rejected": 1,
  "ids": ["…", "…"],
  "errors": [
    {"index": 1, "reason": "missing actor"}
  ]
}
```

## When to use it

- **Backfill / ETL** pipelines that can tolerate skipping corrupt lines
- **Not** for standard LMS real-time ingestion where xAPI-strict behaviour is expected

Standard Moodle / logstore clients should **not** set this flag unless you control
the sender.

See also: [GitHub issue #622](https://github.com/openfun/ralph/issues/622).
