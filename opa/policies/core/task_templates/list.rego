package core.task_templates.list

import data.utils

default allow := false
default is_admin := false
default is_tasks_admin := false
default can_read_source := false

# List of conditions for allowing task templates listing with query
allow if is_admin
allow if is_tasks_admin
allow if {
    not is_admin
    not is_tasks_admin
    query
}

# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

can_read_source if {
    source_id := input.resource.path[1]
    source_response := http.send({
        "method": "GET",
        "headers": {"X-User-Id": input.subject.sub, "X-User-Email": input.subject.email},
        "url": sprintf("http://saltbox-core:8000/task-template-sources/%s", [source_id]),
    })
    source_response.status_code == 200
    source_object := source_response.body
    # Пользователь имеет доступ к источнику шаблонов задач, если у него есть разрешение на чтение в data.permissions
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "task_template_sources",
        "read",
        input.subject,
        source_object
    )
}

query := null if {
    is_admin
}
query := null if {
    not is_admin
    is_tasks_admin
}
query := {"$or": conds} if {
    is_action_list
    not is_admin
    not is_tasks_admin
    can_read_source
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        "task_templates",
        "read",
        input.subject
    )
    count(conds) > 1
}

query := conds[0] if {
    is_action_list
    not is_admin
    not is_tasks_admin
    can_read_source
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        "task_templates",
        "read",
        input.subject
    )
    count(conds) == 1
}

is_action_list if {
    utils.base.is_task_templates_resource
    input.action.name == "list"
    # /task-template-sources/:sid/templates/list
    count(input.resource.path) == 4
    input.resource.path[3] == "list"
}
