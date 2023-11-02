# How to use Ralph as a CLI ?

WIP.

## Prerequisites

- Ralph should be properly installed to be used as a `CLI`. Follow [Installation](../index.md#installation) section for more information
- [**Recommended**] To easily manipulate JSON streams, please [install `jq`](https://jqlang.github.io/jq/download/) on your machine

## `validate` command

In this tutorial, we'll walk you through the process of using `validate` command to check the validity of xAPI statements. 

### With an invalid xAPI statement

First, let's test the `validate` command with a dummy `JSON` string.

- Create in the terminal a dummy statement as follows: 

```bash
invalid_statement='{"foo": "invalid xapi"}'
```

- Run validation on this statement with this command:

```bash
echo "$invalid_statement" | ralph validate -f xapi 
```

- You should observe the following output from the terminal:

```plaintext
INFO     ralph.cli Validating xapi events (ignore_errors=False | fail-on-unknown=False)
ERROR    ralph.models.validator No matching pydantic model found for input event
INFO     ralph.models.validator Total events: 1, Invalid events: 1
```

### With a valid xAPI statement

Now, let's test the `validate` command with a valid xAPI statement.

The tutorial is made on a [`completed video`](https://profiles.adlnet.gov/profile/90b2c849-d744-4d0c-8bd0-403e7859a35b/templates/22d6bb8b-c562-46d7-a773-a01aa179826a) xAPI statement.

???+ info

    According to the specification, an xAPI statement to be valid should contain, at least the three following fields:

    - an `actor` (with a correct [IFI](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#inversefunctional)), 
    - a `verb` (with an [`id`](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#verb) property), 
    - an `object` (with an [`id`](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#object) property).


- Create in the terminal a valid xAPI statement as follows: 

```bash
valid_statement='{"actor": {"mbox": "mailto:johndoe@example.com", "name": "John Doe"}, "verb": {"id": "http://adlnet.gov/expapi/verbs/completed"}, "object": {"id": "http://example.com/video/001-introduction"}, "timestamp": "2023-10-31T15:30:00Z"}'
```

- Run validation on this statement with this command:

``` bash
echo "$valid_statement" | bin/ralph validate -f xapi 
```

- You should observe the following output from the terminal: 

```plaintext
INFO     ralph.cli Validating xapi events (ignore_errors=False | fail-on-unknown=False)
INFO     ralph.models.validator Total events: 1, Invalid events: 1
```

## `convert` command

In this tutorial, you'll learn how to convert OpenEdx events into xAPI statements with Ralph. 

!!! note

    Please note that this feature is currently only supported for a set of OpenEdx events. 
    When converting Edx events to xAPI statements, always refer to the [list of supported event types]() to ensure accurate and successful conversion.

For this example, let's choose the `page_close` OpenEdx event that is converted into a `terminated a page` xAPI statement.

- Create in the terminal a `page_close` OpenEdx event as follows: 

```bash
edx_statements={"username": "", "ip": "0.0.0.0", "agent": "0", "host": "0", "referer": "", "accept_language": "0", "context": {"course_id": "", "course_user_tags": null, "module": null, "org_id": "0", "path": ".", "user_id": null}, "time": "2000-01-01T00:00:00", "page": "http://A.ac/", "event_source": "browser", "session": "", "event": "{}", "event_type": "page_close", "name": "page_close"}
```

- Convert this statement into a `terminated a page` statement with this command:

```bash
echo "$edx_statements" | \ 
ralph convert \
    --platform-url "http://lms-example.com" \
    --uuid-namespace "ee241f8b-174f-5bdb-bae9-c09de5fe017f" \
    --from edx \
    --to xapi | \
    jq
```

- You should observe the following output from the terminal: 

```json
INFO     ralph.cli Converting edx events to xapi format (ignore_errors=False | fail-on-unknown=False)
INFO     ralph.models.converter Total events: 1, Invalid events: 0
{
  "id": "8670c7d4-5485-52bd-b10a-a8ae27a51501",
  "actor": {
    "account": {
      "homePage": "http://lms-example.com",
      "name": "anonymous"
    }
  },
  "verb": {
    "id": "http://adlnet.gov/expapi/verbs/terminated"
  },
  "object": {
    "id": "http://A.ac/",
    "definition": {
      "type": "http://activitystrea.ms/schema/1.0/page"
    }
  },
  "timestamp": "2000-01-01T00:00:00",
  "version": "1.0.0"
}
```

🎉 Congratulations! You just have converted an event generated from OpenEdx LMS to a standardised xAPI statement! 

???+ tip "Store locally converted statements"

    To stored the converted statements locally on your machine, send the output of the `convert` command to a `JSON` file as follows:
    ```bash
    echo "$edx_statements" | \ 
    ralph convert \
        --platform-url "http://lms-example.com" \
        --uuid-namespace "ee241f8b-174f-5bdb-bae9-c09de5fe017f" \
        --from edx \
        --to xapi \
        > converted_event.json
    ```

