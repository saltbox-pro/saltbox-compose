package core.collections.list

import data.utils

default allow := false
default is_admin := false
default is_collections_admin := false
default is_action_list := false
default query := null

# List of conditions for allowing collection listing with query
allow if is_admin
allow if is_collections_admin

allow if {
    not is_admin
    not is_collections_admin
    is_action_list
    query
}

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

query := null if {
    is_admin
}
query := null if {
    not is_admin
    is_collections_admin
}
query := {"$or": conds_with_owner} if {
    not is_admin
    not is_collections_admin
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        "read",
        input.subject
    )
    conds_with_owner := array.concat(conds, [{"owner_id": input.subject.sub}])
    count(conds_with_owner) > 1
}
query := conds_with_owner[0] if {
    not is_admin
    not is_collections_admin
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        "read",
        input.subject
    )
    conds_with_owner := array.concat(conds, [{"owner_id": input.subject.sub}])
    count(conds_with_owner) == 1
}
# query := {
#     "$or": array.concat(
#         [cond |
#             some permission in data.permissions
#             permission.is_active
#             permission.service == input.resource.service_name
#             permission.resource == input.resource.path[0]
#             permission.subject_type == "user"
#             permission.action == "read"
#             utils.conditions.conditions_match(permission.subject_conditions, input.subject)
#             cond := permission.object_conditions
#         ],
#         [{"owner_id": input.subject.sub}]
#     )
# } if {
#     not is_admin
#     not is_collections_admin
# }

# Variables
is_action_list if {
    utils.base.is_collections_resource
    input.action.name == "list"
    count(input.resource.path) == 1
}
