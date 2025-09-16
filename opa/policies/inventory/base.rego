package inventory.base

import data.utils

default allow := false
default is_admin := false
default is_inventory_admin := false

# List of base conditions for allowing inventory actions
allow if is_admin
allow if is_inventory_admin

# Variables
is_admin := utils.base.is_admin
is_inventory_admin := utils.base.is_inventory_admin
