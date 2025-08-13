package core.jobs

default allow := false


allow if is_admin

is_admin if {
    input.subject.roles[_] == "jobs_admin"
}
