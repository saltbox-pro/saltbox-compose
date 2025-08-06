package core.collections.read

import data.core.collections.base
import data.utils.conditions

default allow := false

# Для админов разрешаем все действия, кроме получения default коллекции
# Для default коллекции отдельное правило
allow if {
    base.is_admin
    not is_default_path
}

# Получение default коллекции
# ============================================================
# Для админа возвращает коллекцию с slug "root"
allow if {
    base.is_admin
    is_default_path
    some collection in data.collections
    collection.slug == "root"
}

# Compile Правило для получения default коллекции, на основе разрешений из data.permissions
# Возвращает фильтр с первой разрешенной на чтение коллекцией из data.permissions для роли пользователя
allow if {
    is_default_path
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

# Получение коллекции по slug
# ============================================================
# Правило для полной проверки разрешений на основе условий из data.permissions и атрибутов объекта
allow if {
    base.is_current_resource
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

is_action_read if {
    base.is_current_resource
    input.action.name == "read"
    count(input.resource.path) == 2
}

is_owner if {
    is_action_read
    input.resource.object.owner == input.subject.sub
    input.resource.path[1] == input.resource.object.slug
}

is_default_path if {
    is_action_read
    input.resource.path[1] == "default"
}
