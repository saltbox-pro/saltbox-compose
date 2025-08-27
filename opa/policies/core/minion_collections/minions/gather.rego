package core.minions.gather

import data.utils

default allow := false
default is_admin := false
default is_jobs_admin := false

# List of conditions for allowing collection listing with query
allow if is_admin
allow if is_jobs_admin

# Variables
is_admin := utils.base.is_admin
is_jobs_admin := utils.base.is_jobs_admin
