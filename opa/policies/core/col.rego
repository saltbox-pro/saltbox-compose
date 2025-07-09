package core.col

default allow := false
default is_admin := false

# Admin has all permissions
allow if is_admin

is_admin if {
	some role in input.user.roles
	role == "collections_admin"
}

# List access conditions
allow if {
    input.request.method == "GET"
    input.request.path == ["collections"]
    some role in input.user.roles
    some collection in data.collections
    collection.slug in object.keys(data.collection_roles[role])
}

allow if {
    input.request.method == "GET"
    input.request.path == ["collections"]
    some collection in data.collections
    collection.owner == input.user.sub
}

# Get default collection
allow if {
    input.request.method == "GET"
    count(input.request.path) == 2
    input.request.path == ["collections", "default"]
    some collection in data.collections
    collection.owner == input.user.sub
}

# Read access conditions
# The user can read a collection if has `read` permission on current `slug` in any role
allow if {
    input.request.method == "GET"
    count(input.request.path) == 2
    input.request.path[0] == "collections"
    some role in input.user.roles
    some slug in object.keys(data.collection_roles[role])
    input.request.path[1] == slug
}

# Это подход получения детальной информации о коллекции через partial
# Смысл в том, что в ручку /collections/{slug} мы передаем query {'slug': slug, 'owner': input.user.sub}
# и, по идее, в ответе получаем единственную коллекцию, которая соответствует этому slug и owner
allow if {
    input.request.method == "GET"
    count(input.request.path) == 2
    input.request.path[0] == "collections"
    slug := input.request.path[1]
    some collection in data.collections
    collection.slug == slug
    collection.owner == input.user.sub
}

# Update access conditions
# The user can update a collection if has `update` permission in any role
allow if {
    input.request.method == "PUT"
    count(input.request.path) == 2
    input.request.path[0] == "collections"
    some role in input.user.roles
    some slug in object.keys(data.collection_roles[role])
    input.request.path[1] == slug
    some perm in data.collection_roles[role][input.request.path[1]]
    perm == "update"
}

# The user can update a collection if he is the owner
allow if {
    input.request.method == "PUT"
    count(input.request.path) == 2
    input.request.path[0] == "collections"
    slug := input.request.path[1]
    some collection in data.collections
    collection.slug == slug
    collection.owner == input.user.sub
}
