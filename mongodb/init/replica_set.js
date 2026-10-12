function get_env(name) {
    let val = process.env[name];
    if (typeof(val) == 'undefined') {
        throw new Error(`Not found ${name} environment variable`);
    }
    return val;
}

function ensure_state(is_primary) {
    print(`Waiting MongoDB intance ${is_primary?'':'to not '}to be a writable primary`);
    for (let i = 0; i < 20; i++) {
        if (db.isMaster().isWritablePrimary == is_primary) return;
        sleep(500);
    }
    throw new Error(`Failed to await MongoDB intance ${is_primary?'':'not '}to be a writable primary`);
}

function ensure_member_host(host) {
    const expected_host = `${host}:27017`;
    const cfg = rs.conf();
    const member = cfg.members[0];

    if (member.host == expected_host){
      print(`Replica set member host is already "${expected_host}"`);
      return;
    }
    print(`Replica set member host is "${member.host}", expected "${expected_host}", reconfiguring`);
    member.host = expected_host;
    rs.reconfig(cfg, {force: true});
    ensure_state(is_primary=true);
    print(`Replica set member host has been updated to "${expected_host}"`);
}


function main() {
    const replica_set = get_env('MONGOD_REPLICA_SET');
    const host = get_env('HOSTNAME');
    const adm_db = 'admin';

    use(adm_db);

    print('Ensure replica set');
    try {
        let status = rs.status();
        print(`Replica set status is OK, configured replica set "${status.set}"`);
        ensure_member_host(host);
    } catch (err) {
        if (err.name == 'MongoServerError' && err.codeName == 'NotYetInitialized') {
            rs.initiate({
                _id: replica_set,
                members: [{_id: 0, host: `${host}:27017`}],
            })
            print(`MongoDB instance has been initialized in "${replica_set}" replica set`);
            ensure_state(is_primary=true);
        }
        else {
            print(`Error ${err.name}[${err.codeName}]`);
            throw err;
        }
    }
}

main();
