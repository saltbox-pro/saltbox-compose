package core.collections.default

import data.utils

default allow := false
default query := null
default is_action_read := false
default is_default_path := false

# List of conditions for getting query for default collection
allow if {
    is_action_read
    is_default_path
    query
}

# Variables
is_collections_admin := utils.base.is_collections_admin
is_admin := utils.base.is_admin

query := {"slug": "root"} if {
    is_admin
}
query := {"slug": "root"} if {
    not is_admin
    is_collections_admin
}
query := {
    "$or": array.concat(
        [cond |
            some permission in data.permissions
            permission.is_active
            permission.service == input.resource.service_name
            permission.resource == input.resource.path[0]
            permission.subject_type == "user"
            permission.action == "read"
            utils.conditions.conditions_match(permission.subject_conditions, input.subject)
            cond := permission.object_conditions
        ],
        [{"owner_id": input.subject.sub}]
    )
} if {
    not is_admin
    not is_collections_admin
}

is_action_read if {
    utils.base.is_collections_resource
    input.action.name == "read"
    count(input.resource.path) == 2
}

is_default_path if {
    is_action_read
    input.resource.path[1] == "default"
}
