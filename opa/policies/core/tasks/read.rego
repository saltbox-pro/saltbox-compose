package core.tasks.read

import data.utils

default allow := false
default can_read_task := false
default can_read_collection := false
default is_action_read := false
default is_owner := false

# List of conditions for allowing collection reading
allow if is_admin
allow if is_tasks_admin
allow if can_read_task
allow if is_owner

# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

can_read_task if {
    is_action_read
    task_id := input.resource.path[1]
    task_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/tasks/%s", [task_id]),
    })
    task_response.status_code == 200
    task_object := task_response.body
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        input.action.name,
        input.subject,
        task_object
    )
}

is_action_read if {
    utils.base.is_tasks_resource
    input.action.name == "read"
    count(input.resource.path) == 2
}

is_action_read if {
    utils.base.is_tasks_resource
    input.action.name == "read"
    count(input.resource.path) == 3
    input.resource.path[2] in ["jobs", "returns"]
}

is_owner if {
    is_action_read
    task_id := input.resource.path[1]
    task_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/tasks/%s", [task_id]),
    })
    task_response.status_code == 200
    task_object := task_response.body
    task_object.user.sub == input.subject.sub
}
