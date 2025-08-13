package core.collections.read

import data.core.collections.base
import data.utils.conditions

default allow := false
default can_read_collection := false
default is_action_read := false
default is_owner := false

allow if base.is_admin
allow if can_read_collection
allow if is_owner

# Получение коллекции по slug
# ============================================================
# Правило для полной проверки разрешений на основе условий из data.permissions и атрибутов объекта
can_read_collection if {
    is_action_read
    some permission in data.permissions
    permission.service == input.resource.service_name
    permission.resource == input.resource.path[0]
    permission.action == input.action.name
    # Проверяем условия разрешения
    conditions.conditions_match(permission.object_conditions, input.resource.object)
    conditions.conditions_match(permission.subject_conditions, input.subject)
}

# Variables

is_action_read if {
    base.is_current_resource
    input.action.name == "read"
    count(input.resource.path) == 2
}

is_owner if {
    is_action_read
    input.resource.object.owner_id == input.subject.sub
    input.resource.path[1] == input.resource.object.slug
}

is_default_path if {
    is_action_read
    input.resource.path[1] == "default"
}
