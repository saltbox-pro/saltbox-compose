package core.jobs.schemas.base

import data.utils

default allow := false
default is_admin := false
default is_jobs_admin := false

# List of base conditions for allowing job schemas actions
allow if is_admin
allow if is_jobs_admin

# Variables
is_admin := utils.base.is_admin
is_jobs_admin := utils.base.is_jobs_admin
