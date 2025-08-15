package core.jobs.list

import data.utils

default allow := false
default is_admin := false
default is_jobs_admin := false
default is_action_list := false
default query := null

# List of conditions for allowing collection listing with query
allow if is_admin
allow if is_jobs_admin
allow if {
    not is_admin
    not is_jobs_admin
    is_action_list
    query
}

# Variables
is_admin := utils.base.is_admin
is_jobs_admin := utils.base.is_jobs_admin

# Query не работает, т.к. список job получаем из redis
# Нужно транслировать mongo query и pattern matching
query := null if {
    is_admin
}
query := null if {
    not is_admin
    is_jobs_admin
}
query := {"$or": conds} if {
    not is_admin
    not is_jobs_admin
    conds := [cond |
        some permission in data.permissions
        permission.is_active
        permission.service == input.resource.service_name
        permission.resource == input.resource.path[0]
        permission.subject_type == "user"
        permission.action == "read"
        utils.conditions.conditions_match(permission.subject_conditions, input.subject)
        cond := permission.object_conditions
    ]
    count(conds) > 1
}

query := conds[0] if {
    not is_admin
    not is_jobs_admin
    conds := [cond |
        some permission in data.permissions
        permission.is_active
        permission.service == input.resource.service_name
        permission.resource == input.resource.path[0]
        permission.subject_type == "user"
        permission.action == "read"
        utils.conditions.conditions_match(permission.subject_conditions, input.subject)
        cond := permission.object_conditions
    ]
    count(conds) == 1
}

# Variables
is_action_list if {
    utils.base.is_jobs_resource
    input.action.name == "list"
    count(input.resource.path) == 2
    input.resource.path[1] == "cursored_list"
}
is_action_list if {
    utils.base.is_jobs_resource
    input.action.name == "list"
    count(input.resource.path) == 1
}
