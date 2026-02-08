from sync.sync import Sync

class ModuleBays(Sync): 
   
    api_object = "dcim.module-bays"
    sync_parameters = ["name", "device", "position","description"]
    unique_parameter = ["name","device"]
   
    def pre_sync(self, oldobj, newobj):
        return newobj

    def post_sync(self, oldobj, newobj):
        # we have to check if there is a module installed in the bay and if so install it
        old_module = None
        new_module = None
        
        if oldobj["installed_module"] is not None:
            old_module = self.master_conn.dcim.modules.get(oldobj["installed_module"]["id"])
        if newobj["installed_module"] is not None:   
            new_module = self.slave_conn.dcim.modules.get(newobj["installed_module"]["id"])
            
        if old_module is None and new_module is not None:
            # Remove module
            new_module.delete()
            
        if old_module is not None and new_module is not None:
            diff = False
            if old_module["module_type"]["model"] != new_module["module_type"]["model"]:
                diff = True
            if old_module["serial"] != new_module["serial"]:
                diff = True
            if old_module["status"]["value"] != new_module["status"]["value"]:
                diff = True
            if old_module["module_type"]["manufacturer"]["slug"] != new_module["module_type"]["manufacturer"]["slug"]:
                diff = True
            if diff:
                new_module.delete()
                new_module = None
            
        if old_module is not None and new_module is None:
            payload = {
                "device": newobj["device"]["id"],
                "module_bay": newobj["id"],
                "module_type": {
                    "manufacturer": {
                        "slug": old_module["module_type"]["manufacturer"]["slug"]
                    },
                    "model": old_module["module_type"]["model"]},
                "serial": old_module["serial"],
                "status": old_module["status"]["value"]
                
            }
            self.slave_conn.dcim.modules.create(payload)
            # Install module
       
        
        return newobj