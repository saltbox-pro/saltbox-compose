package core.collections.delete

import data.utils

default allow := false
default is_owner := false
default can_delete_collection := false
default is_root_collection := false

# List of conditions for allowing deletion
allow if {
    is_admin
    not is_root_collection
}
allow if {
    is_collections_admin
    not is_root_collection
}
allow if {
    is_owner
    not is_root_collection
}
allow if can_delete_collection

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

collection := col if {
    is_action_delete
    slug := input.resource.path[1]
    resp := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    resp.status_code == 200
    col := resp.body
}

is_owner if {
    collection_object := collection
    collection_object.owner_id == input.subject.sub
}

can_delete_collection if {
    not is_root_collection
    collection_object := collection
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        "read",
        input.subject,
        collection_object
    )
}

is_action_delete if {
    utils.base.is_collections_resource
    input.action.name == "delete"
    count(input.resource.path) == 2
}

is_root_collection if {
    utils.base.is_collections_resource
    input.resource.path[1] == "root"
}
