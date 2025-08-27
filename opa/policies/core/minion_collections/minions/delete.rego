package core.minions.delete

import data.utils

default allow := false
default is_admin := false
default is_collections_admin := false


# List of conditions for allowing minions listing
allow if is_admin
allow if is_collections_admin

# Variables
is_admin := utils.base.is_admin
is_collections_admin := utils.base.is_collections_admin
