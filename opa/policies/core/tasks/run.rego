package core.tasks.run

import data.utils

default allow := false
default can_run_task := false
default is_action_run := false
default is_owner := false

# List of conditions for allowing task running
allow if is_admin
allow if is_tasks_admin
allow if can_run_task
allow if is_owner

# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

can_run_task if {
    is_action_run
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

is_action_run if {
    utils.base.is_tasks_resource
    input.action.name == "run"
    count(input.resource.path) == 3
    input.resource.path[2] in ["run", "stop", "restart_failed", "restart_failed_on_minion"]
}

is_owner if {
    is_action_run
    task_id := input.resource.path[1]
    task_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/tasks/%s", [task_id]),
    })
    task_response.status_code == 200
    task_object := task_response.body
    task_object.user.sub == input.subject.sub
}
