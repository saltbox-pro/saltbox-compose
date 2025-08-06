package core.collections.list

import data.core.collections.base
import data.utils.conditions

default allow := false

# Allow all actions for collections_admin users
# Except for default collection. For default collection separate rule is applied
allow if base.is_admin

# Compile правило для получения списка коллекций, на основе разрешений из data.permissions
allow if {
    is_action_list
    some collection in data.collections
    some user_role in input.subject.roles
    some permission in data.permissions
    permission.subject_type == "role"
    permission.subject_id == user_role
    permission.service == input.resource.service_name
    permission.resource == input.resource.path[0]
    permission.action == "read"
    slugs := permission.conditions.slug["$in"]
    collection.slug in slugs
}

# Правило для получения списка коллекций, на основе овнерства пользователя
allow if {
    is_action_list
    some collection in data.collections
    collection.owner == input.subject.sub
}

# Variables
is_action_list if {
    base.is_current_resource
    input.action.name == "list"
    count(input.resource.path) == 1
}
