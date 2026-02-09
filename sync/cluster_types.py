from sync.sync import Sync


class ClusterTypes(Sync):

    api_object = "virtualization.cluster_types"
    sync_parameters = ["name", "slug", "description"]
    unique_parameter = ["name"]
    global_sync_values = {}
