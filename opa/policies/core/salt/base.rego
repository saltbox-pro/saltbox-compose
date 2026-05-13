package core.salt.base

import data.utils

default allow := false
default is_admin := false

# List of base conditions for allowing masters actions
allow if is_admin

# Variables
is_admin := utils.base.is_admin
