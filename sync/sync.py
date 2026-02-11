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
        slave_endpoint = self._resolve_api_object(self.slave_conn)
        master_objects = list(master_endpoint.all())
        slave_objects = list(slave_endpoint.all())
        logger.debug(
            "Fetched %d master object(s) and %d slave object(s) for %s",
            len(master_objects),
            len(slave_objects),
            self.api_object,
        )

        self.errors = []
        slave_index = self._build_slave_index(slave_objects)
        sync_plan = self._build_sync_plan(master_objects, slave_index)
        logger.debug("Built sync plan with %d item(s) for %s", len(sync_plan), self.api_object)

        for idx, plan_item in enumerate(sync_plan, start=1):
            master_obj = plan_item["master_obj"]
            try:
                logger.debug(
                    "Applying plan item %d/%d for %s: action=%s, object=%s",
                    idx,
                    len(sync_plan),
                    self.api_object,
                    plan_item["action"],
                    getattr(master_obj, "display", repr(master_obj)),
                )
                new_obj = self._apply_plan_item(slave_endpoint, plan_item)
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
            obj = getattr(obj, part.replace("-", "_"))
        logger.debug("Resolved API object %s", self.api_object)
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

    def _make_hashable(self, value):
        if isinstance(value, dict):
            return tuple(sorted((k, self._make_hashable(v)) for k, v in value.items()))
        if isinstance(value, list):
            return tuple(self._make_hashable(item) for item in value)
        return value

    def _build_unique_key(self, obj):
        key_values = []
        for param in self.unique_parameter:
            value = self.get_unique_field(getattr(obj, param))
            key_values.append(self._make_hashable(value))
        return tuple(key_values)

    def _build_slave_index(self, slave_objects):
        index = {}
        for slave_obj in slave_objects:
            key = self._build_unique_key(slave_obj)
            if key not in index:
                index[key] = slave_obj
        logger.debug("Created slave index with %d unique key(s)", len(index))
        return index

    def _build_sync_plan(self, master_objects, slave_index):
        sync_plan = []
        for master_obj in master_objects:
            try:
                key = self._build_unique_key(master_obj)
                slave_obj = slave_index.get(key)
                if slave_obj is None:
                    logger.info("Object does not exist in slave, creating: %s", getattr(master_obj, "display", repr(master_obj)))
                    payload = self.pre_sync(master_obj, self.create_payload(master_obj))
                    sync_plan.append(
                        {"action": "create", "master_obj": master_obj, "payload": payload}
                    )
                    logger.debug(
                        "Prepared create action for %s with payload keys: %s",
                        getattr(master_obj, "display", repr(master_obj)),
                        sorted(payload.keys()),
                    )
                    continue

                diff = self.get_differences(master_obj, slave_obj)
                diff = self.pre_sync(master_obj, diff)
                if diff:
                    sync_plan.append(
                        {
                            "action": "update",
                            "master_obj": master_obj,
                            "slave_obj": slave_obj,
                            "payload": diff,
                        }
                    )
                    logger.debug(
                        "Prepared update action for %s with changed fields: %s",
                        getattr(master_obj, "display", repr(master_obj)),
                        sorted(diff.keys()),
                    )
                else:
                    sync_plan.append(
                        {"action": "noop", "master_obj": master_obj, "slave_obj": slave_obj}
                    )
                    logger.debug(
                        "Prepared noop action for %s",
                        getattr(master_obj, "display", repr(master_obj)),
                    )
            except Exception as exc:
                identifier = getattr(master_obj, "display", repr(master_obj))
                logger.exception(
                    "Failed to prepare %s sync plan for object %s", self.api_object, identifier
                )
                self.errors.append({"object": identifier, "error": str(exc)})
        return sync_plan

    def _apply_plan_item(self, slave_endpoint, plan_item):
        action = plan_item["action"]
        if action == "create":
            logger.debug("Creating object on slave for %s", getattr(plan_item["master_obj"], "display", repr(plan_item["master_obj"])))
            new_obj = slave_endpoint.create(plan_item["payload"])
            return self.post_create(plan_item["master_obj"], new_obj)

        slave_obj = plan_item["slave_obj"]
        if action == "update":
            logger.debug(
                "Updating slave object %s with fields: %s",
                getattr(slave_obj, "display", repr(slave_obj)),
                sorted(plan_item["payload"].keys()),
            )
            for key, value in plan_item["payload"].items():
                setattr(slave_obj, key, value)
            slave_obj.save()
        if action == "noop":
            logger.debug("No changes required for %s", getattr(slave_obj, "display", repr(slave_obj)))
        return slave_obj

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
        logger.debug(
            "Created payload for %s with fields: %s",
            getattr(obj, "display", repr(obj)),
            sorted(payload.keys()),
        )
        return payload

    def get_differences(self, master_obj, slave_obj):
        diff = {}
        for param in self.sync_parameters:
            master_value = getattr(master_obj, param)
            slave_value = getattr(slave_obj, param)
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
        logger.debug(
            "Calculated diff for %s with changed fields: %s",
            getattr(master_obj, "display", repr(master_obj)),
            sorted(diff.keys()),
        )
        return diff

    def get_unique_field(self, obj):
        if hasattr(obj, "slug"):
            return {"slug": obj.slug}
        elif hasattr(obj, "name"):
            return {"name": obj.name}
        elif hasattr(obj, "value"):
            return obj.value
        elif hasattr(obj, "address"):
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
