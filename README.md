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

### Optional Email Alerts

To receive error logs via email, pass SMTP settings (repeat `--smtp-to` for
multiple recipients). Only error-level logs are emailed.

```bash
python main.py \
  --master-url https://netbox.example/api/ \
  --master-token <MASTER_TOKEN> \
  --slave-url https://netbox.example/api/ \
  --slave-token <SLAVE_TOKEN> \
  --smtp-host smtp.example.com \
  --smtp-port 587 \
  --smtp-user netbox-sync \
  --smtp-password "<SMTP_PASSWORD>" \
  --smtp-from netbox-sync@example.com \
  --smtp-to ops@example.com \
  --smtp-starttls
```

## Testing

```bash
pytest
```

## Notes

- The `Sync` base class encapsulates common diff/creation logic.
- Errors during object sync are logged and do not stop the full sync run.
- Each sync module can override `pre_sync`, `post_sync`, or `post_create` for
  object-specific behavior.
