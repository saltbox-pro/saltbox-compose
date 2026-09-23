package core.tasks.update

import data.utils

default allow := false
default is_admin := false
default is_tasks_admin := false
default can_update_task := false
default is_action_update := false
default is_owner := false

# List of conditions for allowing task updates
allow if is_admin
allow if is_tasks_admin
allow if can_update_task
allow if is_owner

# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

task_from_api := task if {
    is_action_update
    task_id := input.resource.path[1]
    resp := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/tasks/%s", [task_id]),
    })
    resp.status_code == 200
    task := resp.body
}

can_update_task if {
    task_object := task_from_api
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "tasks",
        "update",
        input.subject,
        task_object
    )
}

is_action_update if {
    utils.base.is_tasks_resource
    input.action.name == "update"
    count(input.resource.path) == 2
}

is_owner if {
    task_object := task_from_api
    task_object.user.sub == input.subject.sub
}
