package core.extra_data.items.by_collection

import data.utils

default allow := false
default can_read_collection := false
default is_collection_owner := false

allow if utils.base.is_admin
allow if utils.base.is_collections_admin
allow if can_read_collection
allow if is_collection_owner

collection := col if {
    utils.base.is_extra_data_items_resource
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
