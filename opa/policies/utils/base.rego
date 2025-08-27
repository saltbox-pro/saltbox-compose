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
# Masters and Pillars
# GET /masters list
# GET /masters/{master_id} read
# POST /masters/{mid}/accept accept
# POST /masters/{mid}/reject reject
# GET /pillars list
# POST /pillars create
# PUT /pillars update
# DELETE /pillars delete
# POST /pillars/parse_csv export
# POST /pillars/validate validate
# POST /pillars/import import
# ==========================================
is_masters_admin if {
	some role in input.subject.roles
	role == "masters_admin"
}

is_masters_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "masters"
}

# ==========================================
# Settings
# GET /settings/sls-repos list
# POST /settings/sls-repos create
# POST /settings/sls-repos/sync_all sync_all
# GET /settings/sls-repos/sync-status/{task_id} sync_status
# GET /settings/sls-repos/{sid} read
# PUT /settings/sls-repos/{sid} update
# DELETE /settings/sls-repos/{sid} delete
# POST /settings/sls-repos/{sid}/sync sync
# POST /settings/sls-repos/{sid}/activate activate
# POST /settings/sls-repos/{sid}/deactivate deactivate
# ==========================================
is_settings_admin if {
	some role in input.subject.roles
	role == "settings_admin"
}

is_settings_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "settings"
}

is_git_repos_resource if {
    is_settings_resource
    input.resource.path[1] == "sls-repos"
}

# ==========================================
# Minions
# POST /minions list
# POST /minions/export export
# GET /minions/gather
# GET /minions/{mid} read
# DELETE /minions/{mid} delete
# ==========================================

# ==========================================
# Filters
# GET /filters/schema
# POST /filters/unique-grain-values
# ==========================================
