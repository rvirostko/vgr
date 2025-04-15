# Transfer

def visit_namespaces() -> None:
    LOG.dbg(f'vist_namespaces()')
    data = vault_list(f'/v1/sys/namespaces').get('data', {})
    context: str = 'ns'
    info = data.get('key_info')
    for key in sorted(data.get('keys', [])):
        try:
            ns: dict = info.get(key)
            name: str = normalize_path(key)
            ns['name'] = name
            ns['env'] = env_from_suffix(name)
            DD[context] = ns
            if filter_target(context):
                DD['sn'] = __APP_INFO.get_for_namespace(name)
                if filter_target('sn'):
                    if TARGET == context:
                        format_output()
                    else:
                        if TARGET == 'mount' or TARGET in MOUNT_SUBTYPES: visit_mounts(name)
                        # TODO if there are other things we want to visit within the namespace
                        #      they go here
        finally:
            if context in DD: DD.pop(context)
            if 'sn' in DD: DD.pop('sn')

def visit_mounts(namespace :str) -> None:
    LOG.dbg(f'vist_mounts({namespace})')
    data = vault_get(f'/v1/sys/mounts', namespace).get('data')
    context: str = 'mount'
    for key in sorted(data.keys()):
        try:
            DD[context] = data.get(key)
            name = normalize_path(key)
            DD[context]['name'] = name
            if filter_target(context):
                # If just looking a generic mount, then we are done here
                if TARGET == context:
                    format_output()
                else:
                    # Based on the target and the type of the mount, determine whether and how to visit it
                    mount_type: str = DD[context].get('type', '')
                    if TARGET in MOUNT_TO_TARGET.get(mount_type, []):
                        MOUNT_TYPE_VISITORS.get(mount_type, lambda *args: None)(namespace, name)
        finally:
            if context in DD: DD.pop(context)

 $1 - namespace to check, required
function check_namespace(){
    local v rc namespace
    namespace="${1:?Missing namespace}"
    v=$(vault_list "/v1/sys/namespaces" "$namespace")
    rc=${PIPESTATUS[0]}
    echo "$v"
    if [ $rc -ne 0 ]; then
        log_message "WARN" "Namespace $namespace does not exist"
        return 1
    fi
    return 0
}

# $1 - target namespace (must be URL encoded)
# $2 - optional parent namespace, defaults to root
function create_namespace(){
    local v rc target_namespace parent_namespace
    target_namespace="${1:?Missing target namespace}"
    parent_namespace="${2:-}"
    v=$(vault_post "/v1/sys/namespaces/$target_namespace" "${parent_namespace}" \
        "{\"custom_metadata\": {\"smv_creator\": \"${USER_NAME} at $(date +'%Y-%m%dT%H:%M:%S')\"}}")
    rc=${PIPESTATUS[0]}
    echo "$v"
    if [ $rc -ne 0 ]; then
        log_message "WARN" "Unable to create $target_namespace in ${2:-root}"
        return 1
    fi
    # Just paranoia
    wait_for_vault 2
    return 0
}

# $1 - mount point (must be URL encoded)
# $2 - optional namespace, defaults to root
function check_mount_exists(){
    local v rc namespace mount_point
    mount_point="${1:?Missing mount point}"
    namespace="${2:-}"
    v=$(vault_get "/v1/sys/mounts/$mount_point" "$namespace")
    rc=${PIPESTATUS[0]}
    echo "$v"
    if [ $rc -ne 0 ]; then
        log_message "INFO" "KV2 mount at $mount_point in $namespace does not exist"
        return 1
    fi
    return 0
}

# $1 - mount point (must be URL encoded)
# $2 - optional namespace, defaults to root
function create_kv2_mount(){
    local v rc namespace mount_point
    mount_point="${1:?Missing mount point}"
    namespace="${2:-}"
    v=$(vault_post "/v1/sys/mounts/$mount_point" "$namespace" \
        '{"type":"kv", "options":{"version":"2"}}')
    rc=${PIPESTATUS[0]}
    echo "$v"
    if [ $rc -ne 0 ]; then
        log_message "ERROR" "Unable to create KV2 mount at $mount_point in $namespace"
        return 1
    fi
    # See https://github.com/hashicorp/terraform-provider-vault/issues/677#issuecomment-609116328
    wait_for_vault 10
    return 0
}

# $1 - mount point (must be URL encoded)
# $2 - path (must be URL encoded)
# $3 - kv_data
# $4 - optional namespace, defaults to root
function load_kv2_secret(){
    local v rc namespace mount_point path kv_data
    mount_point="${1:?Missing mount point}"
    path="${2:?Missing path}"
    kv_data="${3:?Missing kv data}"
    namespace="${4:-}"
    v=$(vault_post "/v1/$mount_point/data/$path" "$namespace" "$kv_data")
    rc=${PIPESTATUS[0]}
    echo "$v"
    if [ $rc -ne 0 ]; then
        log_message "ERROR" "Unable to load secrets to $mount_point/$path in $namespace"
        return 1
    fi
    # Just paranoia
    wait_for_vault 2
    return 0
}

# $1 - mount point (must be URL encoded)
# $2 - path (must be URL encoded)
# $3 - meta_data
# $4 - optional namespace, defaults to root
function load_kv2_metadata(){
    mount_point="${1:?Missing mount point}"
    path="${2:?Missing path}"
    meta_data="${3:?Missing meta data}"
    namespace="${4:-}"
    v=$(vault_post "/v1/$mount_point/metadata/$path" "$namespace" "$meta_data")
    rc=${PIPESTATUS[0]}
    echo "$v"
    if [ $rc -ne 0 ]; then
        log_message "ERROR" "Unable to load metadata to $mount_point/$path in $namespace"
        return 1
    fi
    # Just paranoia
    wait_for_vault 2
    return 0
}
