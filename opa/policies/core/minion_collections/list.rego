package core.collections.list

import data.core.collections.base
import data.utils.conditions

default allow := false
default is_action_list := false
default query := null

# Allow all actions for collections_admin users
# Except for default collection. For default collection separate rule is applied
allow if base.is_admin

allow if {
    not base.is_admin
    is_action_list
    query
}

query := null if {
    base.is_admin
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
            conditions.conditions_match(permission.subject_conditions, input.subject)
            cond := permission.object_conditions
        ],
        [{"owner_id": input.subject.sub}]
    )
} if {
    not base.is_admin
}

# Variables
is_action_list if {
    base.is_current_resource
    input.action.name == "list"
    count(input.resource.path) == 1
}
