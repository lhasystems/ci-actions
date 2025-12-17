# Quick Reference Guide

Quick reference for using the dispatch dependency update system.

## For Source Repositories (Send Updates)

### Minimal Setup

```yaml
# .github/workflows/notify-dependencies.yml
name: Notify dependencies

on:
  push:
    paths: ['src/**', 'include/**']

jobs:
  notify:
    uses: lhasystems/ci-actions/.github/workflows/dispatch-dependency-update.yml@main
    with:
      target_repos: 'ec_diffuser'
    secrets:
      dispatch_token: ${{ secrets.DISPATCH_TOKEN }}
```

### Required Secret

`DISPATCH_TOKEN` - Personal access token with `repo` scope

## For Target Repositories (Receive Updates)

### Minimal Setup

```yaml
# .github/workflows/handle-updates.yml
name: Handle updates

on:
  repository_dispatch:
    types: [dependency_update_request]

permissions:
  contents: write
  pull-requests: write

jobs:
  update:
    uses: lhasystems/ci-actions/.github/workflows/handle-dependency-update.yml@main
    with:
      allowed_senders: 'lhasystems/c_lib_control'
    secrets:
      gh_token: ${{ secrets.GITHUB_TOKEN }}
```

### Optional Secret

`PRIVATE_REPO_TOKEN` - For fetching commit logs from private repos

## Common Inputs

### dispatch-dependency-update.yml

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `target_repos` | ✓ | - | Comma-separated repo names |
| `event_type` | - | `dependency_update_request` | Dispatch event type |

### handle-dependency-update.yml

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `allowed_senders` | ✓ | - | Comma-separated full repo paths |
| `manifest_path` | - | `west.yml` | Path to manifest file |
| `update_script_path` | - | Remote URL | Path to update script |

## Common Tasks

### Add Target Repository

In sender workflow:
```yaml
with:
  target_repos: 'ec_diffuser,new_repo'
```

### Add Allowed Sender

In receiver workflow:
```yaml
with:
  allowed_senders: 'lhasystems/c_lib_control,lhasystems/new_sender'
```

### Watch More Paths

In sender workflow, adjust the trigger paths:
```yaml
on:
  push:
    paths: ['src/**', 'include/**', 'west.yml']
```

### Use Local Update Script

In receiver workflow:
```yaml
with:
  update_script_path: 'tools/update_west.py'
```

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Dispatch not received | Check `DISPATCH_TOKEN` has repo scope |
| Unauthorized sender | Add sender to `allowed_senders` |
| No PR created | Verify `contents: write` permission |
| Script not found | Check `update_script_path` or use default |
| No commit log | Add `PRIVATE_REPO_TOKEN` secret |

## Testing

### Manual Trigger
```bash
gh workflow run notify-dependencies.yml
```

### Check Receiver
```bash
gh run list --workflow=handle-updates.yml
```

### Manual Dispatch
```bash
gh api repos/lhasystems/TARGET/dispatches \
  -X POST \
  -f event_type=dependency_update_request \
  -F client_payload[commit]=SHA \
  -F client_payload[sender]=lhasystems/SOURCE \
  -F client_payload[branch]=main
```

## File Locations

| File | Purpose |
|------|---------|
| `.github/workflows/notify-*.yml` | Sender workflow |
| `.github/workflows/handle-*.yml` | Receiver workflow |
| `tools/update_west.py` | Update script (optional local) |
| `west.yml` | Manifest file to update |

## Full Documentation

See [DISPATCH_SYSTEM.md](DISPATCH_SYSTEM.md) for complete documentation.
