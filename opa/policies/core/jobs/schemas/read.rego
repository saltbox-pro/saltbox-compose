package core.jobs.schemas.read

import data.utils

default allow := false
default is_admin := false
default is_jobs_admin := false
default can_read_job_schema := false
default is_action_read := false

# List of conditions for allowing job schema reading
allow if is_admin
allow if is_jobs_admin
allow if can_read_job_schema

# Variables
is_admin := utils.base.is_admin
is_jobs_admin := utils.base.is_jobs_admin

can_read_job_schema if {
    is_action_read
    name := input.resource.path[1]
    job_schema_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/json-schemas/%s", [name]),
    })
    job_schema_response.status_code == 200
    job_schema_object := job_schema_response.body
    # Пользователь может читать схему, если у него есть разрешение на чтение в data.permissions
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        "read",
        input.subject,
        job_schema_object
    )
}

is_action_read if {
    utils.base.is_jobs_schemas_resource
    input.action.name == "read"
    count(input.resource.path) == 2
}
