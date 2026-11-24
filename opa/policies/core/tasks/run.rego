package core.tasks.run

import data.utils

default allow := false
default is_admin := false
default is_tasks_admin := false
default can_run_task := false
default is_action_run := false
default is_owner := false

# List of conditions for allowing task running
allow if is_admin
allow if is_tasks_admin
allow if can_run_task
allow if is_owner
allow if {
    not is_admin
    not is_tasks_admin
    utils.base.is_tasks_resource
    input.action.name == "run"
    input.resource.path == ["tasks", "bulk_stop"]

    request_ids := input.resource.body.task_ids
    is_array(request_ids)
    count(request_ids) > 0
    every task_id in request_ids {
        is_string(task_id)
        regex.match("^[0-9a-fA-F]{24}$", task_id)
    }
    task_ids := {lower(task_id) | some task_id in request_ids}

    resp := http.send({
        "method": "POST",
        "url": "http://saltbox-core:8000/tasks/list",
        "headers": {"Content-Type": "application/json"},
        "body": {"query": {"$or": [{"_id": task_id} | some task_id in task_ids]}},
    })
    resp.status_code == 200
    tasks := resp.body.data
    {task.id | some task in tasks} == task_ids
    every task in tasks {
        user_can_run(task)
    }
}

# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

task_from_api := task if {
    is_action_run
    task_id := input.resource.path[1]
    resp := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/tasks/%s", [task_id]),
    })
    resp.status_code == 200
    task := resp.body
}

can_run_task if has_run_permission(task_from_api)

user_can_run(task) if has_run_permission(task)
user_can_run(task) if is_task_owner(task)

has_run_permission(task) if {
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "tasks",
        "run",
        input.subject,
        task
    )
}

is_action_run if {
    utils.base.is_tasks_resource
    input.action.name == "run"
    count(input.resource.path) == 3
    input.resource.path[2] in ["run", "stop", "restart_failed", "restart_failed_on_minion"]
}

is_owner if is_task_owner(task_from_api)

is_task_owner(task) if task.user.sub == input.subject.sub
