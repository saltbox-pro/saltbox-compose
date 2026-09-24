package core.extra_data.items.update

import data.utils

default allow := false
default is_action := false
default has_permission := false

allow if is_admin
allow if is_collections_admin
allow if has_permission

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

has_permission if {
    is_action
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        input.action.name,
        input.subject,
        input.resource.body
    )
}

is_action if {
    utils.base.is_extra_data_items_resource
    input.action.name == "update"
    count(input.resource.path) == 3
}
