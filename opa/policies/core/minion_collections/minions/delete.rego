package core.minions.delete

import data.utils

default allow := false
default is_admin := false
default is_collections_admin := false
default can_delete_minions := false

# List of conditions for allowing minions deletion
allow if is_admin
allow if is_collections_admin
allow if can_delete_minions

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

can_delete_minions if {
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        input.action.name,
        input.subject,
        delete_object
    )
}

delete_object := {"collection_slug": input.resource.query_params.collection_slug} if {
    utils.base.is_minions_resource
    input.action.name == "delete"
    count(input.resource.path) == 3
    input.resource.path[1] == "delete"
}

delete_object := input.resource.body if {
    utils.base.is_minions_resource
    input.action.name == "delete"
    count(input.resource.path) == 2
    input.resource.path[1] == "bulk_delete"
}
