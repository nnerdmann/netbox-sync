from sync.sync import Sync


class VirtualInterfaces(Sync):

    api_object = "virtualization.interfaces"
    sync_parameters = [
        "name",
        "virtual_machine",
        "enabled",
        "mac_address",
        "mtu",
        "mode",
        "untagged_vlan",
        "description",
    ]
    unique_parameter = ["name", "virtual_machine"]
