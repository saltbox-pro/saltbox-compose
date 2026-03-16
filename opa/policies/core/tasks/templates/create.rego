package core.tasks.templates.create

import data.utils

default allow := false
default is_admin := false
default is_tasks_admin := false
default can_create_task_template := false

allow if is_admin
allow if is_tasks_admin
allow if can_create_task_template


# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin


# Пользователь может создавать шаблоны тасок, если у него есть разрешение на создание в data.permissions
can_create_task if {
    is_action_create
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        input.action.name,
        input.subject,
        input.resource.body
    )
}

is_action_create if {
    utils.base.is_tasks_templates_resource
    input.action.name == "create"
    count(input.resource.path) == 1
}
