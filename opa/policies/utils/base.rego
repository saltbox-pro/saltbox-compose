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

# ==========================================
# Collections
# ==========================================
is_collections_admin if {
    some role in input.subject.roles
    role == "collections_admin"
}

is_collections_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "collections"
}

# ==========================================
# Tasks
# ==========================================
is_tasks_admin if {
	some role in input.subject.roles
	role == "tasks_admin"
}

is_tasks_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "tasks"
}

is_tasks_templates_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "tasks"
    input.resource.path[1] == "template"
}

# ==========================================
# Jobs and Job Schemas
# ==========================================
is_jobs_admin if {
	some role in input.subject.roles
	role == "jobs_admin"
}

is_jobs_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "jobs"
}

is_jobs_schemas_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "json-schemas"
}

# ==========================================
# Masters
# ==========================================
is_masters_admin if {
	some role in input.subject.roles
	role == "masters_admin"
}

is_masters_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "masters"
}
