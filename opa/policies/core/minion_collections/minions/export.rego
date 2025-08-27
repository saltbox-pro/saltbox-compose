package core.minions.export

import data.utils

default allow := false
default is_admin := false
default is_collections_admin := false
default is_action_export := false
default can_read_collection := false
default is_collection_owner := false

# List of conditions for allowing minions listing
allow if is_admin
allow if is_collections_admin
allow if can_read_collection
allow if is_collection_owner

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

collection := col if {
    is_action_export
    slug := input.resource.body.collection_slug
    resp := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    resp.status_code == 200
    col := resp.body
}

can_read_collection if {
    col := collection
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "collections",
        "read",
        input.subject,
        col,
    )
}

is_collection_owner if {
    col := collection
    col.owner_id == input.subject.sub
}

is_action_export if {
    utils.base.is_minions_resource
    input.action.name == "export"
    count(input.resource.path) == 1
}
