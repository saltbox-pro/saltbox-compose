package core.tasks.list

import data.utils

default allow := false
default is_action_list := false
default can_read_collection := false
default query := null

allow if is_admin
allow if is_tasks_admin

allow if {
    not is_admin
    not is_tasks_admin
    is_action_list
    can_read_collection
    query
}

# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

can_read_collection if {
    collection_slug := input.resource.query_params.collection_slug
    collection_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [collection_slug]),
    })
    collection_response.status_code == 200
    collection_object := collection_response.body
    # Пользователь может читать коллекцию, если у него есть разрешение на чтение в data.permissions
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "collections",
        "read",
        input.subject,
        collection_object
    )
}

query := null if {
    is_admin
}
query := null if {
    not is_admin
    is_tasks_admin
}
query := {"$or": conds_with_owner} if {
    can_read_collection
    not is_admin
    not is_tasks_admin
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        "read",
        input.subject
    )
    conds_with_owner := array.concat(conds, [{"user.sub": input.subject.sub}])
    count(conds_with_owner) > 1
}
query := conds_with_owner[0] if {
    can_read_collection
    not is_admin
    not is_tasks_admin
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        "read",
        input.subject
    )
    conds_with_owner := array.concat(conds, [{"user.sub": input.subject.sub}])
    count(conds_with_owner) == 1
}
# Old variant
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
#         [{"user.sub": input.subject.sub}]
#     )
# } if {
#     can_read_collection
#     not is_admin
#     not is_tasks_admin
# }

# Variables
is_action_list if {
    utils.base.is_tasks_resource
    input.action.name == "list"
    count(input.resource.path) == 1
}
