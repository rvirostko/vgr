import os
import argparse
import hvac


class VaultWalker:
    def __init__(self, checker, walk_to="mount"):
        #url = os.environ.get("VAULT_ADDR")
        url = 'http://127.0.0.1:8200'
        #token = os.environ.get("VAULT_TOKEN")
        token = 'hvs.mVwhVUmYjv0wlpdQFOZy6DZo'
        if not url or not token:
            raise RuntimeError("VAULT_ADDR and VAULT_TOKEN must be set in the environment")

        self.client = hvac.Client(url=url, token=token)
        self.checker = checker
        self.walk_to = walk_to

    def list_namespaces(self, namespace=""):
        self.client.adapter.namespace = namespace
        try:
            resp = self.client.adapter.request("LIST", "/v1/sys/namespaces")
            return resp.json().get("data", {}).get("keys", [])
        except Exception:
            return []

    def list_mounts(self, namespace=""):
        self.client.adapter.namespace = namespace
        try:
            return self.client.sys.list_mounted_secrets_engines()
        except Exception:
            return {}

    def walk(self, namespace=""):
        ns_obj = {"namespace": namespace}
        path = ["ns"]
        if not self.checker(path, ns_obj): return
        if self.walk_to == "ns": return
        mounts = self.list_mounts(namespace)
        for mount_obj in mounts.items():
            path_mount = path + ["mount"]
            if not self.checker(path_mount, ns_obj, mount_obj): continue
            if self.walk_to == "mount": continue
            self.walk_mount(path_mount, ns_obj, mount_obj)
        for sub_ns in self.list_namespaces(namespace):
            child_ns = f"{namespace}/{sub_ns}".strip("/")
            self.walk(child_ns)

    def walk_mount(self, path, ns_obj, mount_obj):
        mount_type = mount_obj["data"].get("type")
        if not mount_type: return
        #next_path = path + [mount_type]
        #handler = getattr(self, f"handle_{mount_type}_mount", None)
        #if callable(handler):
        #    handler(next_path, ns_obj, mount_obj)

    def handle_kv_mount(self, path, ns_obj, mount_obj):
        if self.checker(path, ns_obj, mount_obj):
            pass  # stub

    def handle_ldap_mount(self, path, ns_obj, mount_obj):
        if self.checker(path, ns_obj, mount_obj):
            pass  # stub


def xchecker(path, *objs):
    print("→", " > ".join(path))
    for o in objs:
        print('\t', o)
    return True


def main():
    parser = argparse.ArgumentParser(description="Vault namespace/mount walker")
    parser.add_argument(
        "--walk-to", choices=["ns", "mount", "kv", "ldap"],
        default="mount", help="Limit recursion depth"
    )
    args = parser.parse_args()

    walker = VaultWalker(checker=xchecker, walk_to=args.walk_to)
    walker.walk()


if __name__ == "__main__":
    main()
