package core.collections.create

import data.utils

default allow := false
default is_action_create := false
default can_create_collections := false

# List of conditions for allowing collection creation
allow if is_admin
allow if is_collections_admin
allow if can_create_collections

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin

# Правило для полной проверки разрешений на основе условий из data.permissions
# (атрибутов объекта в body и атрибутов юзера)
can_create_collections if {
    is_action_create
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        input.action.name,
        input.subject,
        input.resource.body
    )
}

is_action_create if {
    utils.base.is_collections_resource
    input.action.name == "create"
    count(input.resource.path) == 1
}
