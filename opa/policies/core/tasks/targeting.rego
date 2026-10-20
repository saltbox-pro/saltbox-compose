package core.tasks.targeting

import data.utils

default allow := false
default can_create_task := false
default can_read_collection := false
default is_collection_owner := false

allow if is_admin
allow if is_tasks_admin
allow if {
    can_create_task
    can_read_collection
}
allow if {
    can_create_task
    is_collection_owner
}


# Variables
is_admin := utils.base.is_admin
is_tasks_admin := utils.base.is_tasks_admin

collection := col if {
    slug := input.resource.body.collection_slug
    resp := http.send({
        "method": "GET",
        "headers": {"X-User-Id": input.subject.sub, "X-User-Email": input.subject.email},
        "url": sprintf("http://saltbox-core:8000/collections/%s", [slug]),
    })
    resp.status_code == 200
    col := resp.body
}

# TODO: перейти на GET /collections/{id}, когда основная ручка получения коллекции переедет со slug на id
collection := col if {
    not input.resource.body.collection_slug
    collection_id := input.resource.body.collection_id
    resp := http.send({
        "method": "POST",
        "headers": {"X-User-Id": input.subject.sub, "X-User-Email": input.subject.email},
        "url": "http://saltbox-core:8000/collections/list",
        "body": {"query": {"_id": collection_id}, "limit": 1},
    })
    resp.status_code == 200
    resp.body.total == 1
    col := resp.body.data[0]
}

# 1) Имеет ли доступ к коллекции, по которой строится нацеливание (получаем коллекцию по api)
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

# 2) Имеет ли доступ к созданию тасок
can_create_task if {
    is_action_targeting
    # check_user_permissions(permissions, service_name, resource, action, subject, object) -> bool
    utils.conditions.check_user_permissions(
        data.permissions,
        input.resource.service_name,
        "tasks",
        "create",
        input.subject,
        input.resource.body
    )
}

is_action_targeting if {
    utils.base.is_tasks_resource
    input.action.name == "targeting"
    count(input.resource.path) == 3
    input.resource.path[1] == "targeting"
    input.resource.path[2] == "masters"
}
