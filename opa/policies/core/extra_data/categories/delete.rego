package core.extra_data.categories.delete

import data.utils

default allow := false

# DELETE has no body to check per-object permissions against, so this is a plain role gate
allow if utils.base.is_admin
allow if utils.base.is_collections_admin
