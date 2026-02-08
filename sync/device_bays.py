from sync.sync import Sync

class DeviceBays(Sync): 
   
    api_object = "dcim.device-bays"
    sync_parameters = ["name", "device", "description"]
    unique_parameter = ["name","device"]
   