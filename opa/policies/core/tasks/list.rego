package core.tasks.list

import data.utils

default allow := false
default is_admin := false
default is_tasks_admin := false
default is_action_list := false
default can_read_collection := false
default is_collection_owner := false
default has_collection_access := false
default query := null

allow if is_admin
allow if is_tasks_admin
allow if {
    not is_admin
    not is_tasks_admin
    is_action_list
    has_collection_access
    query
}

# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

collection := col if {
    slug := input.resource.query_params.collection_slug
    resp := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    resp.status_code == 200
    col := resp.body
}

can_read_collection if {
    collection_object := collection
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "collections",
        "read",
        input.subject,
        collection_object
    )
}

is_collection_owner if {
    collection_object := collection
    collection_object.owner_id == input.subject.sub
}

has_collection_access if {
    can_read_collection
}
has_collection_access if {
    is_collection_owner
}

query := null if {
    is_admin
}
query := null if {
    not is_admin
    is_tasks_admin
}
query := {"$or": conds_with_owner} if {
    has_collection_access
    not is_admin
    not is_tasks_admin
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        "tasks",
        "read",
        input.subject
    )
    conds_with_owner := array.concat(conds, [{"user.sub": input.subject.sub}])
    count(conds_with_owner) > 1
}
query := conds_with_owner[0] if {
    has_collection_access
    not is_admin
    not is_tasks_admin
    # get_list_of_conditions(permissions, service_name, resource, action, subject)
    conds := utils.conditions.get_list_of_conditions(
        data.permissions,
        input.resource.service_name,
        "tasks",
        "read",
        input.subject
    )
    conds_with_owner := array.concat(conds, [{"user.sub": input.subject.sub}])
    count(conds_with_owner) == 1
}

# Variables
is_action_list if {
    utils.base.is_tasks_resource
    input.action.name == "list"
    count(input.resource.path) == 1
}
