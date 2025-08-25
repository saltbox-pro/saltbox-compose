package core.masters.base

import data.utils

default allow := false
default is_admin := false
default is_masters_admin := false

# List of base conditions for allowing masters actions
allow if is_admin
allow if is_masters_admin

# Variables
is_admin := utils.base.is_admin
is_masters_admin := utils.base.is_masters_admin
