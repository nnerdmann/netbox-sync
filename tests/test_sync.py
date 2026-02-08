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


def test_get_unique_field_priorities():
    sync = DummySync(None, None)

    assert sync.get_unique_field(SimpleNamespace(slug="core")) == {"slug": "core"}
    assert sync.get_unique_field(SimpleNamespace(name="edge")) == {"name": "edge"}
    assert sync.get_unique_field(SimpleNamespace(value="active")) == "active"
    assert sync.get_unique_field(SimpleNamespace(address="10.0.0.1")) == "10.0.0.1"
    assert sync.get_unique_field("raw") == "raw"


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
