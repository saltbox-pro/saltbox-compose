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
        roles: ['readWriteAnyDatabase'],
    };
    create_user(user);

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
