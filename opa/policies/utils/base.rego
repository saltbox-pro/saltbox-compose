package utils.base

# Defaults
default is_admin := false

default is_collections_admin := false
default is_collections_resource := false
default is_extra_data_categories_resource := false
default is_extra_data_items_resource := false

default is_tasks_admin := false
default is_tasks_resource := false

default is_jobs_admin := false
default is_jobs_resource := false

default is_masters_admin := false
default is_masters_resource := false

default is_settings_admin := false
default is_settings_resource := false
default is_git_repos_resource := false

default is_scheduler_admin := false
default is_scheduler_resource := false

# Variables
is_admin if {
	some role in input.subject.roles
	role == "saltbox_admin"
}

# ==========================================
# Core
# ==========================================
# Collections and Minions
# POST /minions list
# POST /minions/export export
# GET /minions/gather gather
# GET /minions/{mid} read
# DELETE /minions/{mid} delete
# ==========================================
is_collections_admin if {
    some role in input.subject.roles
    role == "collections_admin"
}

is_collections_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "collections"
}

is_minions_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "minions"
}

is_extra_data_categories_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "extra-data"
    input.resource.path[1] == "categories"
}

is_extra_data_items_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "extra-data"
    input.resource.path[1] == "items"
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

is_task_templates_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "task-template-sources"
    input.resource.path[2] == "templates"
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

is_pillars_resource if {
    input.resource.service_name == "core"
    input.resource.path[0] == "pillars"
}

is_pillars_admin if {
    some role in input.subject.roles
    role == "pillars_admin"
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
# Filters
# GET /filters/schema
# POST /filters/unique-grain-values
# ==========================================
is_filters_schema_route if {
    input.resource.service_name == "core"
    input.resource.path[0] == "filters"
    input.resource.path[1] == "schema"
}

is_unique_grain_values_route if {
    input.resource.service_name == "core"
    count(input.resource.path) == 2
    input.resource.path[0] == "filters"
    input.resource.path[1] == "unique-grain-values"
}

# ==========================================
# Scheduler
# ==========================================
is_scheduler_admin if {
    some role in input.subject.roles
    role == "scheduler_admin"
}

# ==========================================
# Inventory
# ==========================================
is_inventory_admin if {
    some role in input.subject.roles
    role == "inventory_admin"
}
