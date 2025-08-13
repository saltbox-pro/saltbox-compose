package core.collections.create

import data.core.collections.base
import data.utils.conditions

default allow := false

# Allow create for admin users
allow if base.is_admin

# Правило для полной проверки разрешений на основе условий из data.permissions
# (атрибутов объекта в body и атрибутов юзера)
allow if {
    base.is_current_resource
    input.action.name == "create"
    some permission in data.permissions
    permission.subject_type == "user"
    permission.service == input.resource.service_name
    permission.resource == input.resource.path[0]
    permission.action == input.action.name
    # Проверяем условия разрешения
    conditions.conditions_match(permission.subject_conditions, input.subject)
    conditions.conditions_match(permission.object_conditions, input.resource.body)
}
