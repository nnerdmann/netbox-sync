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

        master_endpoint = self._resolve_api_object(self.master_conn)
        self.objects = master_endpoint.all()
        self.errors = []

        for master_obj in self.objects:
            try:
                new_obj = self._sync_object(master_obj)
                if new_obj:
                    self.post_sync(master_obj, new_obj)
            except Exception as exc:
                identifier = getattr(master_obj, "display", repr(master_obj))
                logger.exception(
                    "Failed to sync %s object %s", self.api_object, identifier
                )
                self.errors.append({"object": identifier, "error": str(exc)})

        if self.errors:
            logger.warning(
                "Synchronization completed with %d error(s) for %s",
                len(self.errors),
                self.api_object,
            )
        else:
            logger.info("Synchronization process completed")

    def _resolve_api_object(self, connection):
        obj = connection
        for part in self.api_object.split("."):
            obj = getattr(obj, part)
        return obj

    def _build_filter_params(self, master_obj):
        filter_params = {}
        for param in self.unique_parameter:
            unique_value = self.get_unique_field(getattr(master_obj, param))
            if isinstance(unique_value, dict):
                filter_params[param] = next(iter(unique_value.values()))
            else:
                filter_params[param] = unique_value
        return filter_params

    def _sync_object(self, master_obj):
        slave_endpoint = self._resolve_api_object(self.slave_conn)
        filter_params = self._build_filter_params(master_obj)
        existing = slave_endpoint.filter(**filter_params)
        if existing:
            slave_obj = list(existing)[0]
            diff = self.get_differences(master_obj, slave_obj)
            diff = self.pre_sync(master_obj, diff)
            if diff:
                return slave_obj.update(diff)
            return slave_obj

        logger.info("Object does not exist in slave, creating: %s", master_obj.display)
        payload = self.pre_sync(master_obj, self.create_payload(master_obj))
        new_obj = slave_endpoint.create(payload)
        return self.post_create(master_obj, new_obj)
        
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
