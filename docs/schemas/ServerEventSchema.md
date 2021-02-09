<!-- 
    This document has been automatically generated.
    It should NOT BE EDITED.
    To update this part of the documentation,
    please type the following from the repository root:
    $ make docs
-->
# ServerEventSchema

Represents a common server event.

This type of event is triggered from the django middleware on each request excluding:
`/event`, `login`, `heartbeat`, `/segmentio/event` and `/performance`.

## Example

```json
{
    "accept_language": "gu_IN",
    "agent": "Mozilla/5.0 (iPad; CPU iPad OS 10_3_3 like Mac OS X) AppleWebKit/531.1 (KHTML, like Gecko) FxiOS/13.4a3915.0 Mobile/06S690 Safari/531.1",
    "context": {
        "course_id": "course-v1:happen+third+simply",
        "course_user_tags": {
            "hotel": "table"
        },
        "org_id": "happen",
        "path": "/wp-content/posts",
        "user_id": ""
    },
    "event": "{\"POST\": {}, \"GET\": {\"rpp\": [\"50\"], \"page\": [\"1\"]}}",
    "event_source": "server",
    "event_type": "/wp-content/posts",
    "host": "desktop-81.riddle.com",
    "ip": "161.2.124.77",
    "page": null,
    "referer": "http://mayer.biz/",
    "time": "2003-12-25T17:04:11+00:00",
    "username": ""
}
```

## Fields

Name|Type|Required|Nullable|Validation|Documentation
----|----|--------|--------|----------|-------------
accept_language<div id='accept_language'></div>|String|YES|NO|<br>|Consists of the `Accept-Language` HTTP request header.<br><br>    Retrieved with:<br>        `request.META[HTTP_ACCEPT_LANGUAGE]`<br>    Note:<br>        Can be an empty string if the header is not present in the request.<br>        Contains the default language settings of the user.<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L104'>Source</a>
agent<div id='agent'></div>|String|YES|NO|<br>|Consists of the `User-Agent` HTTP request header.<br><br>    Retrieved with:<br>        `request.META[HTTP_USER_AGENT]`<br>    Note:<br>        Can be an empty string if the header is not present in the request.<br>        Contains information about:<br>            Browser name and version<br>            Operating system name and version<br>            Default language<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L108'>Source</a>
<a href='./BaseContextSchema.md'>context</a><div id='context'></div>|Nested|YES|NO|<br>|Consists of a dictionary holding additional information about the request and user.<br><br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/middleware.py#L136'>Source</a>
event<div id='event'></div>|String|YES|NO|<br>Check that the event field contains a parsable JSON string with 2<br>        keys `POST` and `GET` and dictionaries as values. As the event field<br>        is truncated at 512 characters, it might be common that it would not be<br>        parsable.<br>        |Consist of a JSON encoded string holding the content of the GET or POST request.<br><br>    Retrieved with:<br>        `json.dumps({'GET': dict(request.GET), 'POST': dict(request.POST)})[:512]`<br>    Note:<br>        Values for ['password', 'newpassword', 'new_password', 'oldpassword',<br>        'old_password', 'new_password1', 'new_password2'] are replaced by `********`.<br>        The JSON encoded string is truncated at 512 characters resulting in invalid JSON.<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/middleware.py#L75'>Source</a>
event_source<div id='event_source'></div>|String|YES|NO|Equal to `server`<br>|Consists of the value `server`.<br><br>    Note:<br>        Specifies the source of the interaction that triggered the event.<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L105'>Source</a>
event_type<div id='event_type'></div>|Url|YES|NO|Allow relative URL<br>|Consist of the relative URL (without the hostname) of the requested page.<br><br>    Retrieved with:<br>        `request.META['PATH_INFO']`<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L106'>Source</a>
host<div id='host'></div>|String|YES|NO|<br>|Consists of the hostname of the server.<br><br>    Retrieved with:<br>        `request.META[SERVER_NAME]`<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L111'>Source</a>
ip<div id='ip'></div>|Any|YES|NO|<br>Check the IP address is empty or a valid IPv4 address.|Consists of the public IPv4 address of the user.<br><br>    Retrieved with:<br>        `get_ip(request)` cf. https://github.com/un33k/django-ipware/tree/1.1.0<br>    Note:<br>        Can be an empty string if the IP address is not found.<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L102'>Source</a>
page<div id='page'></div>|String|YES|YES|Equal to `None`<br>|Consists of the value `None`.<br><br>    Note:<br>        In JSON the value is `null` instead of `None`.<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L109'>Source</a>
referer<div id='referer'></div>|String|YES|NO|<br>Check referer field empty or a valid URL|Consists of the `Referer` HTTP request header.<br><br>    Retrieved with:<br>        `request.META[HTTP_REFERER]`<br>    Note:<br>        Can be an empty string if the header is not present in the request.<br>        Contains the referring url (previous url visited by the user).<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L103'>Source</a>
time<div id='time'></div>|DateTime|YES|NO|<br>|Consists of the UTC time in ISO format at which the event was emitted.<br><br>    Retrieved with:<br>        `datetime.datetime.utcnow()`<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L110'>Source</a>
username<div id='username'></div>|String|YES|NO|<br>"Check username field empty or 2-30 chars long|Consists of the unique username identifying the logged in user.<br><br>    Retrieved with:<br>        `request.user.username` querying the `auth_user` table.<br>    Note:<br>        Is an empty string when the user is not logged in.<br>        If an exception is raised when retrieving the username from the table then<br>        the value is `anonymous`.<br>        Usernames are made of 2-30 ASCII letters / numbers / underscores (_) / hyphens (-)<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/views/__init__.py#L95'>Source</a>


## Schema validation

### validate_event_type

The event_type should be equal to context.path

