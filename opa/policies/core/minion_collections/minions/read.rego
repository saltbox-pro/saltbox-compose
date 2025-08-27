package core.minions.read

import data.utils

default allow := false
default is_admin := false
default is_collections_admin := false
default is_action_read := false
default can_read_collection := false

# List of conditions for allowing minion reading
allow if is_admin
allow if is_collections_admin
allow if can_read_collection

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

can_read_collection if {
    is_action_read
    slug := input.resource.query_params.collection_slug
    collection_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    collection_response.status_code == 200
    collection_object := collection_response.body
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

is_action_read if {
    utils.base.is_minions_resource
    input.action.name == "read"
    count(input.resource.path) == 2
}
