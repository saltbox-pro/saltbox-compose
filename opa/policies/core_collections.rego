package core.oldcollections

default allow = false

allow if is_admin

# Allow users to get client based on their role collections:retrieve:linux
allow if {
    some role in input.user.roles
    role_parts := split(role, ":")
    count(role_parts) == 3
    role_parts[0] == input.path[0]
    role_parts[1] == input.action
    role_parts[2] == input.path[1]
}

allowed_actions = {action |
    count(input.path) == 2 # check if path has 2 parts e.g. ["clients", "client-slug"]
    some role in input.user.roles
    role_parts := split(role, ":")
    count(role_parts) == 3  # check if role has 3 parts separated by ":" e.g. "clients:retrieve:client-slug"
    role_parts[0] == input.path[0]  # check resource type by first part of path
    role_parts[2] == input.path[1]  # check resource slug by second part of path
    action := role_parts[1]  # return action
}

# Allow users to list clients based on their role
allow if {
    some role in input.user.roles
    role_parts := split(role, ":")
    count(role_parts) == 3
    role_parts[0] == input.path[0]
    role_parts[1] == "retrieve"
    count(input.path) == 1
}

# Return the list of clients slug that the user is allowed to list
allowed_slugs = {client |
    # count(input.path) == 1
    some role in input.user.roles
    role_parts := split(role, ":")
    count(role_parts) == 3
    role_parts[0] == input.path[0]
    client := role_parts[2]
}

# Check if user can create a resource based on their role
allow if can_create

allowed_resource_action = {action |
    count(input.path) == 1 # check if path has 1 part e.g. ["clients"]
    some role in input.user.roles
    role_parts := split(role, ":")
    count(role_parts) > 1  # check if role has 2 parts separated by ":" e.g. "clients:create"
    role_parts[0] == input.path[0]  # check resource type by first part of path
    action := role_parts[1]  # return action
}

can_create if {
    input.method == "POST"
    some role in input.user.roles
    role_parts := split(role, ":")
    count(role_parts) == 2
    role_parts[0] == input.path[0]
    role_parts[1] == "create"
}

is_admin if {
    some role in input.user.roles
    role == "collections_admin"
}
