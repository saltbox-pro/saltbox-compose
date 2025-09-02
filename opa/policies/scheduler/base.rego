package scheduler.base

import data.utils

default allow := false
default is_admin := false
default is_scheduler_admin := false

# List of base conditions for allowing scheduler actions
allow if is_admin
allow if is_scheduler_admin

# Variables
is_admin := utils.base.is_admin
is_scheduler_admin := utils.base.is_scheduler_admin
