package core.minions.merge

import data.utils

default allow := false
default is_admin := false
default is_collections_admin := false
default is_action_merge := false
default can_merge_minions := false

# List of conditions for allowing minions merge
allow if is_admin
allow if is_collections_admin
allow if can_merge_minions

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

can_merge_minions if {
    is_action_merge
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        input.action.name,
        input.subject,
        input.resource.body
    )
}

is_action_merge if {
    utils.base.is_minions_resource
    input.action.name == "merge"
    count(input.resource.path) == 2
    input.resource.path[1] == "merge"
}
