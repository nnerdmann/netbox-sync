from sync.sync import Sync


class Clusters(Sync):

    api_object = "virtualization.clusters"
    sync_parameters = ["name", "type", "group", "site", "tenant", "description"]
    unique_parameter = ["name"]
