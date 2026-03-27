package core.tasks.templates.list

import data.utils

default allow := false
default is_admin := false
default is_tasks_admin := false

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
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        "tasks/template",
        "read",
        input.subject
    )
    count(conds) > 1
}

query := conds[0] if {
    is_action_list
    not is_admin
    not is_tasks_admin
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        "tasks/template",
        "read",
        input.subject
    )
    count(conds) == 1
}

is_action_list if {
    utils.base.is_tasks_templates_resource
    input.action.name == "list"
    count(input.resource.path) == 3
    input.resource.path[2] == "list"
}
