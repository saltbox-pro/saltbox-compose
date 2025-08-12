package core.collections.delete

import data.core.collections.base
import data.utils.conditions

default allow := false
default is_owner := false
default can_delete_collection := false

allow if base.is_admin
allow if is_owner
allow if can_delete_collection

is_owner if {
    is_action_delete
    slug := input.resource.path[1]
    collection_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    collection_response.status_code == 200
    collection_object := collection_response.body
    collection_object.owner_id == input.subject.sub
}

can_delete_collection if {
    is_action_delete
    slug := input.resource.path[1]
    collection_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    collection_response.status_code == 200
    collection_object := collection_response.body
    # Проверяем разрешения для каждой роли пользователя
    # Пользователь может читать коллекцию, если у него есть разрешение на чтение в data.permissions
    some user_role in input.subject.roles
    some permission in data.permissions
    permission.subject_type == "role"
    permission.subject_id == user_role
    permission.service == input.resource.service_name
    permission.resource == "collections"
    permission.action == "delete"
    conditions.conditions_match(permission.conditions, collection_object)
}

is_action_delete if {
    base.is_current_resource
    input.action.name == "delete"
    count(input.resource.path) == 2
}
