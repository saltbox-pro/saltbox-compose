package core.collections

import data.utils.conditions
default allow := false

# Allow all actions for collections_admin users
# Except for default collection. For default collection separate rule is applied
allow if {
    is_admin
    not is_default_path
}

# Compile правило для получения списка коллекций, на основе разрешений из data.permissions
allow if {
    is_current_resource
    input.action.name == "list"
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
    is_current_resource
    input.action.name == "list"
    some collection in data.collections
    collection.owner == input.subject.sub
}

# Compile Правило для получения default коллекции, на основе разрешений из data.permissions
# Возвращает фильтр с первой разрешенной на чтение коллекцией из data.permissions для роли пользователя
allow if {
    is_admin
    is_current_resource
    input.action.name == "read"
    input.resource.path[1] == "default"
    some collection in data.collections
    collection.slug == "root"
}

allow if {
    is_current_resource
    input.action.name == "read"
    input.resource.path[1] == "default"
    some collection in data.collections
    some user_role in input.subject.roles
    some permission in data.permissions
    permission.subject_type == "role"
    permission.subject_id == user_role
    permission.service == input.resource.service_name
    permission.resource == input.resource.path[0]
    permission.action == "read"
    slugs := permission.conditions.slug["$in"]
    collection.slug == slugs[0]
}

# Правило для полной проверки разрешений на основе условий из data.permissions и атрибутов объекта
allow if {
    is_current_resource
    input.action.name == "read"
    # Проверяем разрешения для каждой роли пользователя
    some user_role in input.subject.roles
    some permission in data.permissions

    # Проверяем соответствие разрешения
    permission.subject_type == "role"
    permission.subject_id == user_role
    permission.service == input.resource.service_name
    permission.resource == input.resource.path[0]
    permission.action == input.action.name

    # Проверяем условия разрешения
    conditions.conditions_match(permission.conditions, input.resource.object)
}

# Полная проверка с доступом овнеру к элементу коллекции
allow if is_owner

# Variables
is_owner if {
    is_current_resource
    input.action.name == "read"
    count(input.resource.path) == 2
    input.resource.object.owner == input.subject.sub
    input.resource.path[1] == input.resource.object.slug
}

is_current_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "collections"
}

is_admin if {
	some role in input.subject.roles
	role == "collections_admin"
}

is_default_path if {
    is_current_resource
    count(input.resource.path) == 2
    input.resource.path[1] == "default"
}
