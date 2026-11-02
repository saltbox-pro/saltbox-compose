package core.minions.update

import data.utils

default allow := false
default is_admin := false
default is_collections_admin := false
default is_action_update := false
default can_update_minions := false

# List of conditions for allowing minion update
allow if is_admin
allow if is_collections_admin
allow if can_update_minions

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

can_update_minions if {
    is_action_update
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        input.action.name,
        input.subject,
        object.union(input.resource.body, {"collection_slug": input.resource.query_params.collection_slug})
    )
}

is_action_update if {
    utils.base.is_minions_resource
    input.action.name == "update"
    count(input.resource.path) == 2
}
