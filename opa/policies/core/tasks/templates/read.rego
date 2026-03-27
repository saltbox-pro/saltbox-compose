package core.tasks.templates.read

import data.utils

default allow := false
default is_admin := false
default is_tasks_admin := false
default can_read_task_template := false
default is_action_read := false
default task_template_response := {}
default task_template_object := {}

# List of conditions for allowing task template reading
allow if is_admin
allow if is_tasks_admin
allow if can_read_task_template

# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

can_read_task_template if {
    is_action_read
    task_id := input.resource.path[2]
    task_template_response := http.send({
        "method": "GET",
        "headers": {"X-User-Id": input.subject.sub, "X-User-Email": input.subject.email},
        "url": sprintf("http://saltbox-core:8000/tasks/template/%s", [task_id]),
    })
    task_template_response.status_code == 200
    task_template_object := task_template_response.body
    # Пользователь может читать схему, если у него есть разрешение на чтение в data.permissions
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "tasks/template",
        "read",
        input.subject,
        task_template_object
    )
}

is_action_read if {
    utils.base.is_tasks_templates_resource
    input.action.name == "read"
    count(input.resource.path) == 3
}

is_action_read if {
    utils.base.is_tasks_templates_resource
    input.action.name == "read"
    count(input.resource.path) == 4
    input.resource.path[3] == "with-defaults"
}
