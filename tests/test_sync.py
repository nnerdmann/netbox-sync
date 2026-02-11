from types import SimpleNamespace

from sync.sync import Sync


class DummySync(Sync):
    sync_parameters = ["name", "status", "tags"]
    unique_parameter = ["name"]
    global_sync_values = {"tenant": {"slug": "ipamstuttgartip"}}


class DummyObj:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class DummyEndpoint:
    def __init__(self, objects):
        self._objects = objects
        self.created_payloads = []

    def all(self):
        return self._objects

    def create(self, payload):
        self.created_payloads.append(payload)
        created = DummyObj(**payload)
        self._objects.append(created)
        return created


class DummyConnection:
    def __init__(self, endpoint):
        self.dcim = endpoint


class DummySaveObj(DummyObj):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.save_calls = 0

    def save(self):
        self.save_calls += 1


def test_normalize_value_uses_param_lookup_rules():
    sync = DummySync(None, None)

    assert sync._normalize_value("site", SimpleNamespace(slug="dc1")) == {"slug": "dc1"}
    assert sync._normalize_value("name", "edge") == "edge"
    assert sync._normalize_value("status", SimpleNamespace(value="active")) == "active"
    assert sync._normalize_value("tags", [SimpleNamespace(slug="core")]) == [{"slug": "core"}]


def test_create_payload_includes_globals_and_lists():
    sync = DummySync(None, None)
    obj = DummyObj(
        name="router-1",
        status=SimpleNamespace(value="active"),
        tags=[SimpleNamespace(slug="core"), SimpleNamespace(slug="edge")],
    )

    payload = sync.create_payload(obj)

    assert payload == {
        "name": "router-1",
        "status": "active",
        "tags": [{"slug": "core"}, {"slug": "edge"}],
        "tenant": {"slug": "ipamstuttgartip"},
    }


def test_get_differences_detects_changes():
    sync = DummySync(None, None)
    master = DummyObj(
        name="router-1",
        status=SimpleNamespace(value="active"),
        tags=[],
        tenant=SimpleNamespace(slug="ipamstuttgartip"),
    )
    slave = DummyObj(
        name="router-1",
        status=SimpleNamespace(value="planned"),
        tags=[],
        tenant=SimpleNamespace(slug="ipamstuttgartip"),
    )

    diff = sync.get_differences(master, slave)

    assert diff == {"status": "active"}


def test_build_filter_params_handles_unique_fields():
    sync = DummySync(None, None)
    obj = DummyObj(
        name="device-a",
        status=SimpleNamespace(value="active"),
    )

    assert sync._build_filter_params(obj) == {"name": "device-a"}


def test_sync_continues_on_errors():
    class FailingSync(DummySync):
        api_object = "dcim"

        def pre_sync(self, oldobj, newobj):
            if oldobj.name == "bad":
                raise RuntimeError("boom")
            return newobj

    master_objects = [
        DummyObj(name="good", status=SimpleNamespace(value="active"), tags=[]),
        DummyObj(name="bad", status=SimpleNamespace(value="active"), tags=[]),
        DummyObj(name="good-2", status=SimpleNamespace(value="active"), tags=[]),
    ]
    conn = DummyConnection(DummyEndpoint(master_objects))
    sync = FailingSync(conn, conn)

    sync.sync()

    assert len(sync.errors) == 1


def test_sync_uses_offline_plan_and_save_for_updates():
    class OfflineSync(DummySync):
        api_object = "dcim"
        sync_parameters = ["name", "status"]
        unique_parameter = ["name"]
        global_sync_values = {}

    master_objects = [
        DummyObj(name="device-a", status=SimpleNamespace(value="active")),
        DummyObj(name="device-b", status=SimpleNamespace(value="planned")),
    ]
    slave_objects = [
        DummySaveObj(name="device-a", status=SimpleNamespace(value="offline")),
    ]

    master = DummyConnection(DummyEndpoint(master_objects))
    slave_endpoint = DummyEndpoint(slave_objects)
    slave = DummyConnection(slave_endpoint)

    sync = OfflineSync(master, slave)
    sync.sync()

    updated_obj = slave_objects[0]
    assert updated_obj.status == "active"
    assert updated_obj.save_calls == 1
    assert slave_endpoint.created_payloads == [{"name": "device-b", "status": "planned"}]


def test_build_sync_plan_with_demo_data():
    class OfflineSync(DummySync):
        api_object = "dcim"
        sync_parameters = ["name", "status"]
        unique_parameter = ["name"]
        global_sync_values = {}

    sync = OfflineSync(None, None)
    demo_master_data = [
        DummyObj(name="demo-rtr-1", status=SimpleNamespace(value="active")),
        DummyObj(name="demo-rtr-2", status=SimpleNamespace(value="active")),
    ]
    demo_slave_data = [
        DummyObj(name="demo-rtr-1", status=SimpleNamespace(value="planned")),
    ]

    slave_index = sync._build_slave_index(demo_slave_data)
    plan = sync._build_sync_plan(demo_master_data, slave_index)

    assert [item["action"] for item in plan] == ["update", "create"]
    assert plan[0]["payload"] == {"status": "active"}
    assert plan[1]["payload"] == {"name": "demo-rtr-2", "status": "active"}
