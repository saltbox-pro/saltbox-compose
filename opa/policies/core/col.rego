package core.col

default allow := false
default is_admin := false


# Admin has all permissions
allow if is_admin

is_admin if {
	some role in input.subject.roles
	role == "collections_admin"
}

# List access conditions
allow if {
    input.action.method == "GET"
    input.resource.path == ["collections"]
    some role in input.subject.roles
    some collection in data.collections
    collection.slug in object.keys(data.collection_roles[role])
}

allow if {
    input.action.method == "GET"
    input.resource.path == ["collections"]
    some collection in data.collections
    collection.owner == input.subject.sub
}

# Get default collection
allow if {
    input.action.method == "GET"
    count(input.resource.path) == 2
    input.resource.path == ["collections", "default"]
    some collection in data.collections
    collection.owner == input.subject.sub
}

# Read access conditions
# The user can read a collection if has `read` permission on current `slug` in any role
allow if {
    input.action.method == "GET"
    count(input.resource.path) == 2
    input.resource.path[0] == "collections"
    some role in input.subject.roles
    some slug in object.keys(data.collection_roles[role])
    input.resource.path[1] == slug
}

# Это подход получения детальной информации о коллекции через partial
# Смысл в том, что в ручку /collections/{slug} мы передаем query {'slug': slug, 'owner': input.user.sub}
# и, по идее, в ответе получаем единственную коллекцию, которая соответствует этому slug и owner
allow if {
    input.action.method == "GET"
    count(input.resource.path) == 2
    input.resource.path[0] == "collections"
    slug := input.resource.path[1]
    some collection in data.collections
    collection.slug == slug
    collection.owner == input.subject.sub
}

# Update access conditions
# The user can update a collection if has `update` permission in any role
allow if {
    input.action.method == "PUT"
    count(input.resource.path) == 2
    input.resource.path[0] == "collections"
    some role in input.subject.roles
    some slug in object.keys(data.collection_roles[role])
    input.resource.path[1] == slug
    some perm in data.collection_roles[role][input.resource.path[1]]
    perm == "update"
}

# The user can update a collection if he is the owner
allow if {
    input.action.method == "PUT"
    count(input.resource.path) == 2
    input.resource.path[0] == "collections"
    slug := input.resource.path[1]
    some collection in data.collections
    collection.slug == slug
    collection.owner == input.subject.sub
}
