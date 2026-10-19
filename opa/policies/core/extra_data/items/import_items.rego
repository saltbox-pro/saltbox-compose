package core.extra_data.items.import_items

import data.utils

default allow := false
default can_import := false
default can_read_collection := false
default is_collection_owner := false

allow if is_admin
allow if is_collections_admin
allow if {
    can_import
    can_read_collection
}
allow if {
    can_import
    is_collection_owner
}

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

collection := col if {
    slug := input.resource.body.fields.collection_slug
    resp := http.send({
        "method": "GET",
        "headers": {"X-User-Id": input.subject.sub, "X-User-Email": input.subject.email},
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

can_import if {
    is_action_import
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        input.action.name,
        input.subject,
        input.resource.body.fields
    )
}

is_action_import if {
    utils.base.is_extra_data_items_resource
    input.action.name == "import"
    count(input.resource.path) == 3
    input.resource.path[2] == "import"
}
