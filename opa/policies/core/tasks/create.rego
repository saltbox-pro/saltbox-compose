package core.tasks.create

import data.utils

default allow := false
default can_create_task := false
default can_read_collection := false
default is_collection_owner := false
default can_read_task_template := false

allow if is_admin
allow if is_tasks_admin
allow if {
    can_create_task
    can_read_collection
    can_read_task_template
}
allow if {
    can_create_task
    is_collection_owner
    can_read_task_template
}


# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

collection := col if {
    slug := input.resource.body.collection_slug
    resp := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    resp.status_code == 200
    col := resp.body
}

# 1) Имеет ли доступ к коллекции по которой создается таска (получаем коллекцию по api) или является ее овнером
can_read_collection if {
    collection_object := collection
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "collections",
        "read",
        input.subject,
        collection_object
    )
}

# 1.1) Является ли пользователь овнером коллекции
is_collection_owner if {
    collection_object := collection
    collection_object.owner_id == input.subject.sub
}

# 2) Имеет ли доступ к шаблону таски (получаем шаблон таски по api)
can_read_task_template if {
    tpl_id := input.resource.body.task_template_id
    task_template_response := http.send({
        "method": "GET",
        "url": sprintf("http://saltbox-core:8000/tasks/template/%s", [tpl_id]),
    })
    task_template_response.status_code == 200
    task_template_object := task_template_response.body
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "tasks/template",
        "read",
        input.subject,
        task_template_object
    )
}

# 3) Имеет ли доступ к созданию тасок
# Пользователь может создавать таски, если у него есть разрешение на создание в data.permissions
can_create_task if {
    is_action_create
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        input.resource.path[0],
        input.action.name,
        input.subject,
        input.resource.body
    )
}

is_action_create if {
    utils.base.is_tasks_resource
    input.action.name == "create"
    count(input.resource.path) == 1
}
