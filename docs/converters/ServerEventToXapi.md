<!-- 
    This document has been automatically generated.
    It should NOT BE EDITED.
    To update this part of the documentation,
    please type the following from the repository root:
    $ make docs
-->
# ServerEventToXapi

Converts a common edX server event to xAPI
Example Statement: John viewed https://www.fun-mooc.fr/ Web page

## Schema: [ServerEventSchema](./../schemas/ServerEventSchema.md)

## Example

```json
{
    "actor": {
        "account": {
            "homePage": "https://fun-mooc.fr",
            "name": "student"
        },
        "objectType": "Agent"
    },
    "context": {
        "extensions": {
            "https://www.edx.org/extension/accept_language": "gu_IN",
            "https://www.edx.org/extension/agent": "Mozilla/5.0 (iPad; CPU iPad OS 10_3_3 like Mac OS X) AppleWebKit/531.1 (KHTML, like Gecko) FxiOS/13.4a3915.0 Mobile/06S690 Safari/531.1",
            "https://www.edx.org/extension/course_id": "course-v1:happen+third+simply",
            "https://www.edx.org/extension/course_user_tags": {
                "hotel": "table"
            },
            "https://www.edx.org/extension/host": "desktop-81.riddle.com",
            "https://www.edx.org/extension/ip": "161.2.124.77",
            "https://www.edx.org/extension/org_id": "happen",
            "https://www.edx.org/extension/path": "/wp-content/posts",
            "https://www.edx.org/extension/request": "{\"POST\": {}, \"GET\": {\"rpp\": [\"50\"], \"page\": [\"1\"]}}"
        },
        "platform": "https://fun-mooc.fr"
    },
    "object": {
        "definition": {
            "name": {
                "en": "page"
            },
            "type": "http://activitystrea.ms/schema/1.0/page"
        },
        "id": "https://fun-mooc.fr/wp-content/posts",
        "objectType": "Activity"
    },
    "timestamp": "2003-12-25T17:04:11+00:00",
    "verb": {
        "display": {
            "en": "viewed"
        },
        "id": "http://id.tincanapi.com/verb/viewed"
    },
    "version": "1.0.3"
}
```

## Conversion table

Name|Value
----|----
actor>account>homePage|https://fun-mooc.fr
actor>account>name|GetFromField([context](./../schemas/ServerEventSchema.md#user-content-context)>[user_id](./../schemas/BaseContextSchema.md#user-content-user_id), lambda user_id: str(user_id) if user_id else "student",)
actor>objectType|Agent
context>extensions>https://www.edx.org/extension/accept_language|GetFromField([accept_language](./../schemas/ServerEventSchema.md#user-content-accept_language))
context>extensions>https://www.edx.org/extension/agent|GetFromField([agent](./../schemas/ServerEventSchema.md#user-content-agent))
context>extensions>https://www.edx.org/extension/course_id|GetFromField([context](./../schemas/ServerEventSchema.md#user-content-context)>[course_id](./../schemas/BaseContextSchema.md#user-content-course_id))
context>extensions>https://www.edx.org/extension/course_user_tags|GetFromField([context](./../schemas/ServerEventSchema.md#user-content-context)>[course_user_tags](./../schemas/BaseContextSchema.md#user-content-course_user_tags))
context>extensions>https://www.edx.org/extension/host|GetFromField([host](./../schemas/ServerEventSchema.md#user-content-host))
context>extensions>https://www.edx.org/extension/ip|GetFromField([ip](./../schemas/ServerEventSchema.md#user-content-ip))
context>extensions>https://www.edx.org/extension/org_id|GetFromField([context](./../schemas/ServerEventSchema.md#user-content-context)>[org_id](./../schemas/BaseContextSchema.md#user-content-org_id))
context>extensions>https://www.edx.org/extension/path|GetFromField([context](./../schemas/ServerEventSchema.md#user-content-context)>[path](./../schemas/BaseContextSchema.md#user-content-path))
context>extensions>https://www.edx.org/extension/request|GetFromField([event](./../schemas/ServerEventSchema.md#user-content-event))
context>platform|https://fun-mooc.fr
object>definition>name>en|page
object>definition>type|http://activitystrea.ms/schema/1.0/page
object>id|GetFromField([event_type](./../schemas/ServerEventSchema.md#user-content-event_type), lambda event_type: self.platform + event_type)
object>objectType|Activity
timestamp|GetFromField([time](./../schemas/ServerEventSchema.md#user-content-time))
verb>display>en|viewed
verb>id|http://id.tincanapi.com/verb/viewed
version|1.0.3


