package core.collections.read

import data.utils

default allow := false
default can_read_collection := false
default is_action_read := false
default is_owner := false
default can_create_tasks := false

# List of conditions for allowing collection reading
allow if is_admin
allow if is_collections_admin
allow if can_read_collection
allow if is_owner

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

collection := col if {
    is_action_read
    slug := input.resource.path[1]
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
        input.resource.path[0],
        input.action.name,
        input.subject,
        collection_object
    )
}

is_action_read if {
    utils.base.is_collections_resource
    input.action.name == "read"
    count(input.resource.path) == 2
}

is_owner if {
    collection_object := collection
    collection_object.owner_id == input.subject.sub
}
