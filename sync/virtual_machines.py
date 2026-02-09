from sync.sync import Sync


class VirtualMachines(Sync):

    api_object = "virtualization.virtual_machines"
    sync_parameters = [
        "name",
        "cluster",
        "status",
        "role",
        "tenant",
        "platform",
        "vcpus",
        "memory",
        "disk",
        "description",
    ]
    unique_parameter = ["name", "cluster"]
