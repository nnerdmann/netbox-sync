from sync.sync import Sync

class Racks(Sync): 
   
    api_object = "dcim.racks"
    sync_parameters = ["name", "site", "location","role","rack_type","status"]
    unique_parameter = ["name"]
   