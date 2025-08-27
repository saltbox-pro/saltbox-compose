package core.tasks.read

import data.utils

default allow := false
default is_admin := false
default is_tasks_admin := false
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

task_from_api := task if {
    is_action_read
    task_id := input.resource.path[1]
    resp := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/tasks/%s", [task_id]),
    })
    resp.status_code == 200
    task := resp.body
}

can_read_task if {
    task_object := task_from_api
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "tasks",
        "read",
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
    task_object := task_from_api
    task_object.user.sub == input.subject.sub
}
