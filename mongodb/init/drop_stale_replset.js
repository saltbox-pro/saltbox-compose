function get_env(name) {
    let val = process.env[name];
    if (typeof(val) == 'undefined') {
        throw new Error(`Not found ${name} environment variable`);
    }
    return val;
}

function main() {
    const replica_set = get_env('MONGOD_REPLICA_SET');

    use('local');

    if (
        db.system.replset.countDocuments({}) > 0
            && db.system.replset.countDocuments({_id: replica_set}) == 0
    ) {
        let existing_replica_set = db.system.replset.findOne({})._id;
        print(`Requested replica set name "${replica_set}" does not match existing replica set "${existing_replica_set}"`)
        print('Dropping hard existing replica set config');
        db.dropDatabase()
    } else {
        print('Current replica set looks OK');
    }
}

main();
