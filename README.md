# NetBox Sync

Sync objects between two NetBox instances using the NetBox API.

## Project Structure

- `main.py`: CLI entry point for running a sync.
- `sync/`: Sync implementations per object type and base sync logic.
- `tests/`: Unit tests for core sync behavior.

## Setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

For development tooling and tests:

```bash
pip install -r requirements-dev.txt
```

## Usage

```bash
python main.py \
  --master-url https://netbox.example/api/ \
  --master-token <MASTER_TOKEN> \
  --slave-url https://netbox.example/api/ \
  --slave-token <SLAVE_TOKEN>
```

## Testing

```bash
pytest
```

## Notes

- The `Sync` base class encapsulates common diff/creation logic.
- Each sync module can override `pre_sync`, `post_sync`, or `post_create` for
  object-specific behavior.
