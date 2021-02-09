<!-- 
    This document has been automatically generated.
    It should NOT BE EDITED.
    To update this part of the documentation,
    please type the following from the repository root:
    $ make docs
-->
# BaseContextSchema

Represents the Base Context inherited by all event contexts.

## Fields

Name|Type|Required|Nullable|Validation|Documentation
----|----|--------|--------|----------|-------------
course_id<div id='course_id'></div>|String|YES|NO|<br>|Consists of the unique identifier for the visited course page.<br><br>    Retrieved with:<br>        `course_id.to_deprecated_string()` where `course_id` is an<br>        `opaque_keys.edx.locator.CourseLocator` which is created using the URL<br>        of the requested page.<br>    Note:<br>        Is an empty string when the requested page is not a course page.<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/contexts.py#L54'>Source</a>
course_user_tags<div id='course_user_tags'></div>|Dict|NO|NO|<br>|Consists of a dictionary with key value pairs from the `user_api_usercoursetag` table.<br><br>    Retrieved with:<br>        `dict(<br>            UserCourseTag.objects.filter(<br>                user=request.user.pk, course_id=course_key<br>            ).values_list('key', 'value')<br>        )`<br>    Note:<br>        Is only present when a course page is requested.<br>        Is an empty dictionary when the user is not logged in or not found in the<br>        `user_api_usercoursetag` table.<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/openedx/core/djangoapps/user_api/middleware.py#L38-L46'>Source</a>
org_id<div id='org_id'></div>|String|YES|NO|<br>|Consists of the organization name that lists the course.<br><br>    Retrieved with:<br>        `course_id.org` where `course_id` is an `opaque_keys.edx.locator.CourseLocator`<br>        which is created using the URL of the requested page.<br>    Note:<br>        Is an empty string when the requested page is not a course page.<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/contexts.py#L55'>Source</a>
path<div id='path'></div>|Url|YES|NO|Allow relative URL<br>|Consist of the relative URL (without the hostname) of the requested page.<br><br>    Retrieved with:<br>        `request.META['PATH_INFO']`<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/middleware.py#L143'>Source</a>
user_id<div id='user_id'></div>|Any|YES|YES|<br>"Check user_id field is None, an empty string or an integer|Consists of the ID of the authenticated user.<br><br>    Retrieved with:<br>        `request.user.pk` querying the `auth_user` table.<br>    Note:<br>        Is an integer when the user is found in the `auth_user` table.<br>        Is an empty string when an exception is raised while retrieving the id.<br>        Is `None` when the user is not logged in.<br>    <a href='https://github.com/openfun/edx-platform/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f/common/djangoapps/track/middleware.py#L189'>Source</a>


## Schema validation

### validate_course_id

The course_id should be equal to
"course-v1:{org_id}+{any_string}+{any_string}"
or be an empty string if org_id is an empty string

