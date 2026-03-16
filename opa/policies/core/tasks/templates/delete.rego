package core.tasks.templates.delete

import data.utils

default allow := false
default is_admin := false
default is_tasks_admin := false
default can_delete_task_template := false

allow if is_admin
allow if is_tasks_admin
allow if can_delete_task_template


# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin


# Пользователь может удалять шаблоны тасок, если у него есть разрешение на создание в data.permissions
can_delete_task if {
    is_action_delete
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

is_action_delete if {
    utils.base.is_tasks_templates_resource
    input.action.name == "delete"
    count(input.resource.path) == 2
}
