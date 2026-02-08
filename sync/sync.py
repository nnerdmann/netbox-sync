import logging


logger = logging.getLogger(__name__)


class Sync:

    api_object = None
    sync_parameters = []
    unique_parameter = []
    global_sync_values = {"tenant": {"slug": "ipamstuttgartip"}}
    
    def __init__(self, master_conn, slave_conn, mapping_file=None):
        self.master_conn = master_conn
        self.slave_conn = slave_conn
        self.mapping_file = mapping_file

    def sync(self):
        logger.info("Starting synchronization process for %s", self.api_object)
        
        parts = self.api_object.split('.')
        obj = self.master_conn
        for part in parts:
            obj = getattr(obj, part)
        self.objects = obj.all()
        
        for master_obj in self.objects:
            slave_obj = self.slave_conn
            for part in parts:
                slave_obj = getattr(slave_obj, part)
            filter_params = {param: next(iter(self.get_unique_field(getattr(master_obj, param)).values())) if isinstance(self.get_unique_field(getattr(master_obj, param)), dict) else self.get_unique_field(getattr(master_obj, param)) for param in self.unique_parameter}
            existing = slave_obj.filter(**filter_params)
            if existing:
                slave_obj = list(existing)[0]
                diff = self.get_differences(master_obj,slave_obj)
                diff = self.pre_sync(master_obj,diff)
                if diff:                 
                    new_obj = slave_obj.update(diff)
                else:
                    new_obj = slave_obj
            else:
                logger.info("Object does not exist in slave, creating: %s", master_obj.display)
                payload = self.pre_sync(master_obj,self.create_payload(master_obj))
                new_obj = slave_obj.create(payload)
                new_obj = self.post_create(master_obj,new_obj)
                
            
            if obj is None:
                continue
    
            if new_obj:
                new_obj = self.post_sync(master_obj, new_obj)
        logger.info("Synchronization process completed")
        
    def create_payload(self, obj):
        """Create payload from master object for synchronization."""
        payload = {}
        for param in self.sync_parameters:
            value = getattr(obj, param)
            if isinstance(value, list):
                payload[param] = [self.get_unique_field(item) for item in value]
            else:
                payload[param] = self.get_unique_field(value)

        for key, val in self.global_sync_values.items():
            payload[key] = val
        return payload
    
    def get_differences(self, master_obj, slave_obj):
        diff = {}
        for param in self.sync_parameters:
            master_value = getattr(master_obj, param)
            slave_value = getattr(slave_obj, param)
            # Compare slug if values are objects, otherwise compare directly
            # master_val = {"slug":master_value.slug} if hasattr(master_value, 'slug') else master_value
            # slave_val = {"slug":slave_value.slug} if hasattr(slave_value, 'slug') else slave_value
            master_val = self.get_unique_field(master_value)
            slave_val = self.get_unique_field(slave_value)
            if master_val != slave_val:
                logger.info(
                    "Difference found in %s: Master(%s) != Slave(%s)",
                    param,
                    master_val,
                    slave_val,
                )
                diff[param] = master_val

        for key, val in self.global_sync_values.items():
            if hasattr(slave_obj, key) is False:
                continue
            slave_val = getattr(slave_obj, key)
            # Compare val against slave_val's dictionary representation
            slave_val_dict = self.get_unique_field(slave_val)
            if val != slave_val_dict:
                logger.info(
                    "Global difference found in %s: Master(%s) != Slave(%s)",
                    key,
                    val,
                    slave_val_dict,
                )
                diff[key] = val
        
        if len(diff) == 0:
            return False
        return diff
    
    def get_unique_field(self,obj):
        if hasattr(obj, 'slug'):
            return {"slug":obj.slug} 
        elif hasattr(obj, 'name'):
            return {"name":obj.name}
        elif hasattr(obj, 'value'):
            return obj.value
        elif hasattr(obj, 'address'):
            return obj.address
        else:
            return obj
        
    def pre_sync(self, oldobj, newobj):
        # Placeholder for pre-sync processing
        return newobj    
    
    def post_sync(self, oldobj, newobj):
        # Placeholder for post-sync processing
        return newobj
    
    def post_create(self, oldobj, newobj):
        # Placeholder for post-create processing
        return newobj
