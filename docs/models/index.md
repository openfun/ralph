# Learning statement models

The learning statement models validation and conversion tools in Ralph empower you to work with an LRS and ensure the quality of xAPI statements.
These features not only enhance the integrity of your learning data but also facilitate integration and compliance with industry standards.

This section provides insights into the supported models, their conversion, and validation.

## Supported statements

Learning statement models encompass a wide array of xAPI and OpenEdx statement types, ensuring comprehensive support for your e-learning data.

1. **xAPI statements models**:
    - [LMS](https://profiles.adlnet.gov/profile/c4e8732c-428a-4aa0-9585-91bebcdea91d)
    - [Video](https://profiles.adlnet.gov/profile/90b2c849-d744-4d0c-8bd0-403e7859a35b)
    - [Virtual classroom](https://profiles.adlnet.gov/profile/4719f43e-28ef-4108-b76a-5fbde91c6f68)

2. **OpenEdx statements models**:
    - [Enrollment](https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#enrollment-events)
    - [Navigational](https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#course-navigation-events)
    - [Open Reponse Assessment](https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#open-response-assessment-events)
    - [Peer instruction](https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#peer-instruction-events)
    - [Problem interaction](https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#problem-interaction-events)
    - [Textbook interaction](https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#textbook-interaction-events)
    - [Video interaction](https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#video-interaction-events)

## Statements validation

In learning analytics, the validation of statements takes on significant importance. 
These statements, originating from diverse sources, systems or applications, must align with specific standards such as [xAPI](https://xapi.com/) for the best known. 
The validation process becomes essential in ensuring that these statements meet the required standards, facilitating data quality and reliability. 

Ralph allows you to automate the validation process in your production stack. 
OpenEdx related events and xAPI statements are supported.

!!! warning 

    For now, validation is effective only with supported [learning statement models](#learning-statement-models) on Ralph. About xAPI statements, an [issue](https://github.com/openfun/ralph/issues/388) is open to extend validation to any xAPI statement.

Check out tutorials to test the validation feature:

- [`validate` with Ralph as a CLI](../tutorials/cli.md#validate-command)
- [`validate` with Ralph as a library](../tutorials/library.md#validate-method)

## Statements conversion

Ralph currently supports conversion from OpenEdx learning events to xAPI statements. Here is the up-to-date conversion sets availables: 

| FROM | TO |
|---|---|
|[edx.course.enrollment.activated]|[registered to a course]|
|[edx.course.enrollment.deactivated]|[unregistered to a course]|
|[load_video/edx.video.loaded]|[initialized a video]|
|[play_video/edx.video.played]|[played a video]|
|[pause_video/edx.video.paused]|[paused a video]|
|[stop_video/edx.video.stopped]|[terminated a video]|
|[seek_video/edx.video.position.changed]|[seeked in a video]|

Check out tutorials to test the conversion feature:

- [`convert` with Ralph as a CLI](../tutorials/cli.md#convert-command)
- [`convert` with Ralph as a library](../tutorials/library.md#convert-method)

[edx.course.enrollment.activated]: https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#edx-course-enrollment-activated-and-edx-course-enrollment-deactivated
[edx.course.enrollment.deactivated]: https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#edx-course-enrollment-activated-and-edx-course-enrollment-deactivated

[load_video/edx.video.loaded]:https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#load-video-edx-video-loaded
[play_video/edx.video.played]: https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#play-video-edx-video-played
[pause_video/edx.video.paused]: https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#pause-video-edx-video-paused
[stop_video/edx.video.stopped]: https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#stop-video-edx-video-stopped
[seek_video/edx.video.position.changed]: https://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs/student_event_types.html#seek-video-edx-video-position-changed

[registered to a course]: https://profiles.adlnet.gov/profile/d0f8a66c-df56-4cb4-bfaf-10c2febd87a1/templates/685a9da1-0d8c-4ae5-82bf-fff7b601c288
[unregistered to a course]: https://profiles.adlnet.gov/profile/d0f8a66c-df56-4cb4-bfaf-10c2febd87a1/templates/685a9da1-0d8c-4ae5-82bf-fff7b601c288

[initialized a video]: https://profiles.adlnet.gov/profile/90b2c849-d744-4d0c-8bd0-403e7859a35b/templates/117b577e-5d35-40c1-b062-96bc912c0106
[played a video]: https://profiles.adlnet.gov/profile/90b2c849-d744-4d0c-8bd0-403e7859a35b/templates/e25acdb9-813e-4b1a-93bc-8dea1eac83ce
[paused a video]: https://profiles.adlnet.gov/profile/90b2c849-d744-4d0c-8bd0-403e7859a35b/templates/6fd56cdf-794f-4ecd-b21c-0cbc109491b3
[seeked in a video]: https://profiles.adlnet.gov/profile/90b2c849-d744-4d0c-8bd0-403e7859a35b/templates/d0ee8f46-5704-428c-b21e-b583f99cd571
[terminated a video]: https://profiles.adlnet.gov/profile/90b2c849-d744-4d0c-8bd0-403e7859a35b/templates/ac270a91-7629-49a8-b5a0-832dcbf30e4c
