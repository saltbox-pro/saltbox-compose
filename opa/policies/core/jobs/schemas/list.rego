package core.jobs.schemas.list

import data.utils

default allow := false
default is_admin := false
default is_jobs_admin := false

# List of conditions for allowing job schemas listing with query
allow if is_admin
allow if {
    is_jobs_admin
    is_action_list
    query
}
allow if {
    not is_admin
    not is_jobs_admin
    is_action_list
    query
}

# Variables
is_admin := utils.base.is_admin
is_jobs_admin := utils.base.is_jobs_admin

query := null if {
    is_admin
}
# query := null if {
#     not is_admin
#     is_jobs_admin
# }
query := {"$or": conds} if {
    not is_admin
    # not is_jobs_admin
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        "read",
        input.subject
    )
    count(conds) > 1
}

query := conds[0] if {
    not is_admin
    # not is_jobs_admin
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        "read",
        input.subject
    )
    count(conds) == 1
}

is_action_list if {
    utils.base.is_jobs_schemas_resource
    input.action.name == "list"
    count(input.resource.path) == 1
}
