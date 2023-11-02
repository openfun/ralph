# Upgrade

All instructions to upgrade this project from one release to the next will be documented in this file. Upgrades must be run sequentially, meaning you should not skip minor/major releases while upgrading (fix releases can be skipped).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### 3.x.x to 4.0.0

#### Upgrade user credentials
To conform to xAPI specifications, we need to represent users as xAPI Agents. You must therefore delete and re-create the credentials file using the updated cli, OR you can modify it directly to add the `agents` field. The credentials file is located in `{ RALPH_APP_DIR }/{ RALPH_AUTH_FILE }` (defaults to `.ralph/auth.json`). Each user profile must follow the following pattern (see [this post](https://xapi.com/blog/deep-dive-actor-agent/) for examples of valid agent objects) :

```
{
  "username": "USERNAME_UNCHANGED",
  "hash": "PASSWORD_HASH_UNCHANGED",
  "scopes": [ LIST_OF_SCOPES_UNCHANGED ],
  "agent": { A_VALID_AGENT_OBJECT }
}
```
Agent can take one of the following forms, as specified by the [xAPI specification](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#2423-inverse-functional-identifier):
- mbox: 
```
"agent": {
      "mbox": "mailto:john.doe@example.com"
}
```
- mbox_sha1sum:
```
"agent": {
        "mbox_sha1sum": "ebd31e95054c018b10727ccffd2ef2ec3a016ee9",
}
```
- openid:
```
"agent": {
      "openid": "http://foo.openid.example.org/"
}
```
- account:
```
"agent": {
      "account": {
        "name": "simonsAccountName",
        "homePage": "http://www.exampleHomePage.com"
}
```

For example here is a valid `auth.json` file: 

```
[
  {
    "username": "john.doe@example.com",
    "hash": "$2b$12$yBXrzIuRIk6yaft5KUgVFOIPv0PskCCh9PXmF2t7pno.qUZ5LK0D2",
    "scopes": ["example_scope"],
    "agent": {
      "mbox": "mailto:john.doe@example.com"
    }
  },
  {
    "username": "simon.says@example.com",
    "hash": "$2b$12$yBXrzIuRIk6yaft5KUgVFOIPv0PskCCh9PXmF2t7pno.qUZ5LK0D2",
    "scopes": ["second_scope", "third_scope"],
    "agent": {
      "account": {
        "name": "simonsAccountName",
        "homePage": "http://www.exampleHomePage.com"
      }
    }
  }
]
```

#### Upgrade history syntax

CLI syntax has been changed from `fetch` & `push` to `read` & `write` affecting the command history. You must replace the command history after updating:
- locate your history file path, which is in `{ RALPH_APP_DIR }/history.json` (defaults to `.ralph/history.json`)
- run the commands below to update history

```bash
sed -i 's/"fetch"/"read"/g' { my_history_file_path }
sed -i 's/"push"/"write"/g' { my_history_file_path }
```

#### Upgrade ClickHouse schema

If you are using the ClickHouse backend, schema changes have been made
to drop the existing JSON column in favor of the String version of the 
same data. See [this issue](https://github.com/openfun/ralph/issues/482) 
for details. 

Ralph does not manage the ClickHouse schema, so if you have existing 
data you will need to manually alter it as an admin user. Note: this 
will rewrite the statements table, which may take a long time if you
have many rows. The command to run is:

```sql
-- If RALPH_BACKENDS__DATA__CLICKHOUSE__DATABASE is 'xapi'
-- and RALPH_BACKENDS__DATA__CLICKHOUSE__EVENT_TABLE_NAME is 'test'

ALTER TABLE xapi.test DROP COLUMN event, RENAME COLUMN event_str to event;
```
