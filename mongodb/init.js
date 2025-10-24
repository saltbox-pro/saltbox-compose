var get_env = function(name) {
    let val = process.env[name];
    if (typeof(val) == 'undefined') {
        throw new Error(`Not found ${name} environment variable`);
    }
    return val;
}

var ensure_primary = function() {
    for (let i = 0; i < 20; i++) {
        if (db.isMaster().isWritablePrimary) return;
        sleep(500);
    }
    throw new Error("Failed to await MongoDB intance to be a writable primary");
}

var main = function() {
    const username = get_env("MONGO_ADMIN_USERNAME");
    const password = get_env("MONGO_ADMIN_PASSWORD");
    const replica_set = get_env("MONGOD_REPLICA_SET");
    const host = get_env("HOSTNAME");
    const adm_db = "admin";

    use(adm_db);

    print('Ensure replica set');
    try {
        rs.status();
        print(`MongoDB instance already in replica set "${replica_set}"`);
    } catch (err) {
        if (err.name == "MongoServerError" && err.codeName == "NotYetInitialized") {
            rs.initiate({
                _id: replica_set,
                members: [{_id: 0, host: `${host}:27017`}],
            })
            print(`MongoDB instance has been initialized in "${replica_set}" replica set`);
            ensure_primary();
        }
        // TODO On hostname change
        // else if (err.name == "MongoServerError" && err.codeName == "InvalidReplicaSetConfig")
        // FIXME else if (err.name == "MongoServerError" && err.codeName == "InvalidReplicaSetConfig")
        else {
            print(`Error ${err.name}[${err.codeName}]`);
            //FIXME throw err;
        }
    }

    print('Ensure admin');
    if (db.getUsers({filter: {'user': username}}).users.length == 0) {
        db.createUser(
            {
                user: username,
                pwd: password,
                roles: [{role: "userAdminAnyDatabase", db: adm_db}, "readWriteAnyDatabase"]
            }
        )
        print(`MongoDB user "${username}" has been created`);
    } else {
        print(`MongoDB user "${username}" already exists`);
    }
}

main();
