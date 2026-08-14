# Partial success on bulk POST (issue #622)

By default, `POST /xAPI/statements` is **atomic**: if one statement in the batch
fails validation, the entire request is rejected (HTTP `400` / `422`) and **no**
statement from the batch is stored.

For large historical backfills (e.g. Open edX tracking logs → ClickHouse / ES),
losing a 10 000-statement batch because of a single malformed event is costly.

Partial success is therefore available, **disabled by default**. It is activated by
either of these two triggers:

| Trigger | Scope | Set by |
|---------|-------|--------|
| `?partialSuccess=true` or `?ignoreInvalid=true` | one request | the client |
| `RALPH_LRS_PARTIAL_SUCCESS_DEFAULT=true` (default `false`) | the whole instance | the server |

Clients that cannot add a query parameter — the Moodle `logstore_xapi` plugin is the
typical case — are only covered by the server setting. See
[Enabling it on the server](#enabling_it_on_the_server) below.

Once the server default is on, a client can still force xAPI-strict behaviour per
request with `?partialSuccess=false`.

## Behaviour

| Mode | Invalid statement in batch | HTTP | Body |
|------|---------------------------|------|------|
| Default (xAPI-strict) | Any | `400` / `422` | Error detail — **nothing stored** |
| `partialSuccess=true` | Some | `200` | Report with `inserted`, `rejected`, `ids`, `errors` |
| `partialSuccess=true` | All | `400` | Report with `inserted: 0` |

In partial-success mode, statements that pass Pydantic validation but are rejected
by Elasticsearch (e.g. dynamic mapping errors) are skipped individually: the batch
still returns HTTP `200` when at least one statement is indexed.

## Enabling it on the server

Set the variable wherever your instance reads its configuration.

In a `.env` file:

```bash
RALPH_LRS_PARTIAL_SUCCESS_DEFAULT=true
```

With `docker run`:

```bash
docker run … -e RALPH_LRS_PARTIAL_SUCCESS_DEFAULT=true fundocker/ralph:… \
  runserver -b es
```

With Docker Compose:

```yaml
services:
  lrs:
    image: fundocker/ralph:5.0.3-beta1
    environment:
      RALPH_LRS_PARTIAL_SUCCESS_DEFAULT: "true"
```

Compose does not restart a container when only its environment changes, so apply it
with:

```bash
docker compose up -d --force-recreate lrs
```

### Checking the setting was picked up

An environment variable that never reaches the process is the most common cause of
"nothing changed". Ask the running instance what it sees:

```bash
docker compose exec lrs python -c \
  "from ralph.conf import settings; print(settings.LRS_PARTIAL_SUCCESS_DEFAULT)"
```

This must print `True`. If it prints `False`, the variable did not reach the process:
check the `RALPH_` prefix, that the `env_file` is loaded, and that the container was
recreated rather than merely restarted.

### Rolling back

The setting is a plain switch with no data migration:

```bash
RALPH_LRS_PARTIAL_SUCCESS_DEFAULT=false
```

To try partial success on a single request without touching the server
configuration, send `?partialSuccess=true` instead.

### Elasticsearch-compatible dict keys (`5.0.3-beta1`)

When `RUNSERVER_BACKEND=es` and `RALPH_LRS_ELASTICSEARCH_VALIDATE_KEYS=true` (default),
statements with incompatible JSON object keys are rejected during API validation (before
ES indexation), with an explicit `errors[]` reason in partial-success mode:

| Key | Example | Rejected? |
|-----|---------|-----------|
| Empty string | `""` in quiz match extension | Yes |
| Non-IRI with `.` | `nested.key` in extension value map | Yes |
| xAPI IRI | `http://id.tincanapi.com/extension/quiz` | No (dots in URL are OK) |

Environment:

```bash
RALPH_LRS_ELASTICSEARCH_VALIDATE_KEYS=true   # default
RALPH_RUNSERVER_BACKEND=es
```

!!! warning "Turn partial success on first"

    In strict mode this check rejects the whole batch *before* any write, so nothing
    is indexed. Up to `5.0.2-beta1` such a batch returned HTTP 500 while the valid
    statements were still written to Elasticsearch. If your deployment relies on that
    partial write, enable `RALPH_LRS_PARTIAL_SUCCESS_DEFAULT` before upgrading.

Empty keys are what a Moodle quiz "match" question produces when a pairing is left
without an answer. You can reproduce it with two statements, one valid and one
carrying an empty extension key:

```bash
curl -u ralph:secret \
  -X POST 'http://localhost:8100/xAPI/statements/?partialSuccess=true' \
  -H 'Content-Type: application/json' \
  -H 'X-Experience-API-Version: 1.0.3' \
  -d '[
    {"actor":{"mbox":"mailto:a@example.com","objectType":"Agent"},"verb":{"id":"http://adlnet.gov/expapi/verbs/experienced"},"object":{"id":"https://example.com/1"}},
    {"actor":{"mbox":"mailto:b@example.com","objectType":"Agent"},"verb":{"id":"http://adlnet.gov/expapi/verbs/answered"},"object":{"id":"https://example.com/quiz"},"result":{"extensions":{"http://id.tincanapi.com/extension/quiz":{"":"unmatched"}}}}
  ]'
```

Response (`200`) — the first statement is indexed, the second is named precisely:

```json
{
  "inserted": 1,
  "rejected": 1,
  "errors": [
    {
      "index": 1,
      "reason": "elasticsearch-incompatible key: empty string at result.extensions.http://id.tincanapi.com/extension/quiz"
    }
  ]
}
```

The `reason` field is what lets you trace the faulty activity back in the LMS. Without
this check the same batch fails with an opaque `elasticsearch indexation failed`.

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

Standard Moodle / logstore clients cannot set the query flag themselves. Enabling
partial success for them means setting `RALPH_LRS_PARTIAL_SUCCESS_DEFAULT=true` on
the server, which applies to **every** client of that instance — only do it when you
own the deployment and accept non-atomic batches for all senders.

See also: [GitHub issue #622](https://github.com/openfun/ralph/issues/622).
