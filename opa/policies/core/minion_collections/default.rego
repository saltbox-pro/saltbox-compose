package core.collections.default

import data.core.collections.base
import data.utils.conditions

default allow := false
default query := null

# Compile Правило для получения default коллекции, на основе разрешений из data.permissions
# Возвращает фильтр с первой разрешенной на чтение коллекцией из data.permissions для роли пользователя
allow if {
    is_action_read
    is_default_path
    query
}

# Variables
query := {"slug": "root"} if {
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

is_action_read if {
    base.is_current_resource
    input.action.name == "read"
    count(input.resource.path) == 2
}

is_default_path if {
    is_action_read
    input.resource.path[1] == "default"
}
