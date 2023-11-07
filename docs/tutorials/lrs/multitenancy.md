
# Multitenancy

By default, all authenticated users have full read and write access to the server. Ralph LRS implements the specified [Authority mechanism](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#249-authority) to restrict behavior.

## Filtering results by authority (multitenancy)

In Ralph LRS, all incoming statements are assigned an `authority` (or ownership) derived from the user that makes the request. You may restrict read access to users "own" statements (thus enabling multitenancy) by setting the following environment variable: 

```bash title=".env"
RALPH_LRS_RESTRICT_BY_AUTHORITY=True # Default: False
```

!!! warning
    Two accounts with different credentials may share the same `authority`, meaning they can access the same statements. It is the administrator's responsibility to ensure that `authority` is properly assigned.

!!! info
    If not using "scopes", or for users with limited "scopes", using this option will make the use of option `?mine=True` implicit when fetching statement.

### Scopes

In Ralph, users are assigned scopes which may be used to restrict endpoint access or 
functionalities. You may enable this option by setting the following environment variable:

```bash title=".env"
RALPH_LRS_RESTRICT_BY_SCOPES=True # Default: False
```

Valid scopes are a slight variation on those proposed by the
[xAPI specification](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Communication.md#details-15):

- statements/write
- statements/read/mine
- statements/read
- state/write
- state/read
- define
- profile/write
- profile/read
- all/read
- all
