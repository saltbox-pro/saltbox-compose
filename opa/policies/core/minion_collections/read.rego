package core.collections.read

import data.utils

default allow := false
default can_read_collection := false
default is_action_read := false
default is_owner := false

# List of conditions for allowing collection reading
allow if is_admin
allow if is_collections_admin
allow if can_read_collection
allow if is_owner

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

can_read_collection if {
    is_action_read
    slug := input.resource.path[1]
    collection_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    collection_response.status_code == 200
    collection_object := collection_response.body
    # Пользователь может читать коллекцию, если у него есть разрешение на чтение в data.permissions
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
    is_action_read
    slug := input.resource.path[1]
    collection_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    collection_response.status_code == 200
    collection_object := collection_response.body
    collection_object.owner_id == input.subject.sub
}
