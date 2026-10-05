function get_env(name, strict=true) {
    let val = process.env[name];
    if (strict && val === undefined) {
        throw new Error(`Not found ${name} environment variable`);
    }
    return val;
}

function create_user(user) {
    db.createUser(user);
    print(`MongoDB user "${user.user}" has been created`);
}

function main() {
    const root_password = get_env('MONGO_ROOT_PASSWORD');
    const root_username = get_env('MONGO_ROOT_USERNAME');
    const user_password = get_env('MONGO_USER_PASSWORD');
    const user_username = get_env('MONGO_USER_USERNAME');
    const user_db = get_env('MONGO_USER_DB');
    // Module users are optional, empty when the module is disabled
    const scheduler_username = get_env('MONGO_SCHEDULER_USERNAME', strict=false);
    const scheduler_db = get_env('MONGO_SCHEDULER_DB', strict=false);
    const migration_username = get_env('MONGO_MIGRATION_USERNAME', strict=false);
    const migration_db = get_env('MONGO_MIGRATION_DB', strict=false);
    // Exporter user is optional
    const exporter_username = get_env('MONGO_EXPORTER_USERNAME', strict=false);
    const adm_db = 'admin';
    const local_db = 'local'

    if (user_username == root_username) {
        throw new Error('MONGO_ROOT_USERNAME must differ from MONGO_USER_USERNAME');
    }

    use(adm_db);

    print('Delete existing users')
    db.dropAllUsers();

    print('Create users');
    const root = {
        user: root_username,
        pwd: root_password,
        roles: [{role: 'root', db: adm_db}],
    };
    create_user(root);

    const user = {
        user: user_username,
        pwd: user_password,
        roles: [{role: 'readWrite', db: user_db}],
    };
    create_user(user);

    if (scheduler_username) {
        const scheduler_password = get_env('MONGO_SCHEDULER_PASSWORD');
        create_user({
            user: scheduler_username,
            pwd: scheduler_password,
            roles: [{role: 'readWrite', db: scheduler_db}],
        });
    }

    if (migration_username) {
        const migration_password = get_env('MONGO_MIGRATION_PASSWORD');
        create_user({
            user: migration_username,
            pwd: migration_password,
            roles: [{role: 'readWrite', db: migration_db}],
        });
    }

    if (exporter_username !== undefined) {
        const exporter_password = get_env('MONGO_EXPORTER_PASSWORD');
        if (exporter_password == '') {
            throw new Error(`No password for exporter user ${exporter_username}`);
        }
        const exporter = {
            user: exporter_username,
            pwd: exporter_password,
            roles: [
                { role: 'read', db: adm_db },
                { role: 'clusterMonitor', db: adm_db },
                { role: 'read', db: local_db }
            ]
        };
        create_user(exporter);
    }
}

main();

// vi: sw=4
