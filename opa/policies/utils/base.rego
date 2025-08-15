package utils.base

# Defaults
default is_admin := false

default is_collections_admin := false
default is_collections_resource := false

default is_tasks_admin := false
default is_tasks_resource := false

default is_jobs_admin := false
default is_jobs_resource := false

# Variables
is_admin if {
	some role in input.subject.roles
	role == "saltbox_admin"
}

is_collections_admin if {
    some role in input.subject.roles
    role == "collections_admin"
}

is_collections_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "collections"
}

is_tasks_admin if {
	some role in input.subject.roles
	role == "tasks_admin"
}

is_tasks_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "tasks"
}

is_jobs_admin if {
	some role in input.subject.roles
	role == "jobs_admin"
}

is_jobs_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "jobs"
}
