package core.git_repos.base

import data.utils

default allow := false
default is_admin := false
default is_settings_admin := false

# List of conditions for allowing collection listing with query
allow if is_admin
allow if is_settings_admin

# Variables
is_admin := utils.base.is_admin
is_settings_admin := utils.base.is_settings_admin
