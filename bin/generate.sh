#!/bin/bash

# Generates random xAPI statements using ralph generate command

file_name=../xapi_generated.json
nb_of_users=100
nb_of_events_by_session=20
nb_of_schools=1
event_type_pattern=Video

user_homePage=https://www.fun-mooc.fr/

> $file_name

for school_number in $(seq $nb_of_schools); do
    school="school_${school_number}"
    course="course_${school_number}"
    module="module_${school_number}"
    video_uuid=a41d5caf-5310-42ee-b74c-8a942c778f6d
    for user_name in $(seq $nb_of_users); do
        session_uuid=$(uuidgen)
        echo $user_name
        ralph -v DEBUG generate -f xapi -c $nb_of_events_by_session -p $event_type_pattern -o "\
actor__account__name=${user_name},\
actor__account__homePage=${user_homePage},\
context__extensions__https://w3id.org/xapi/video/extensions/session-id=${session_uuid},\
object__definition__extensions__http://adlnet.gov/expapi/activities/course=${course},\
object__definition__extensions__http://adlnet.gov/expapi/activities/module=${module},\
object__definition__extensions__https://w3id.org/xapi/acrossx/extensions/school=${school},\
object__id=uuid://${video_uuid}" >> $file_name
    done
done
cat $file_name
cat ../xapi_generated.json | ralph -v DEBUG push -b es --es-index statements-marsha-test --es-hosts "http://localhost:9200"