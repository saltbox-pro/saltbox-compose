package core.collections.move

import data.utils

default allow := false
default is_owner := false
default is_action_move := false
default can_update_collection := false

# List of conditions for allowing collection moving
allow if is_admin
allow if is_collections_admin
allow if can_update_collection
allow if is_owner

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

# TODO: the move request body only carries `target_id` (no slug), so the slug-based
# `GET /collections/{slug}` lookup used by the other collection policies doesn't apply here.
# Resolving the target through the generic list endpoint instead. Switch to a direct
# id-based fetch once collection lookups are migrated from slug to id.
collection := col if {
    is_action_move
    target_id := input.resource.body.target_id
    resp := http.send({
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "url": "http://saltbox-core:8000/collections/list",
        "body": {"query": {"_id": target_id}},
    })
    resp.status_code == 200
    col := resp.body.data[0]
}

is_owner if {
    collection_object := collection
    collection_object.owner_id == input.subject.sub
}

can_update_collection if {
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

is_action_move if {
    utils.base.is_collections_resource
    input.action.name == "update"
    count(input.resource.path) == 2
    input.resource.path[1] == "move"
}
