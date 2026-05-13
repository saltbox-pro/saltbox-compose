package core.salt.keys.action

import data.utils

default allow := false

allow if is_admin

# Variables
is_admin := utils.base.is_admin
