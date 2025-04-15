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
