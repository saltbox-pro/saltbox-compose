package core.collections.create

import data.core.collections.base
import data.utils.conditions

default allow := false

# Allow create for admin users
allow if base.is_admin

# Правило для полной проверки разрешений на основе условий из data.permissions и атрибутов объекта
allow if {
    base.is_current_resource
    input.action.name == "create"
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
    conditions.conditions_match(permission.conditions, input.resource.body)
}
