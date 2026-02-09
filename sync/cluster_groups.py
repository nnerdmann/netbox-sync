from sync.sync import Sync


class ClusterGroups(Sync):

    api_object = "virtualization.cluster_groups"
    sync_parameters = ["name", "slug", "description"]
    unique_parameter = ["name"]
    global_sync_values = {}
