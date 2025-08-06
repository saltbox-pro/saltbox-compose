package core.collections.base

# Variables
is_current_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "collections"
}

is_admin if {
	some role in input.subject.roles
	role == "collections_admin"
}
