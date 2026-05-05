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
      gh_app_id: ${{ secrets.GH_APP_ID }}
      gh_app_private_key: ${{ secrets.GH_APP_PRIVATE_KEY }}
```

### Required Secrets

- `GH_APP_ID` - GitHub App numeric ID
- `GH_APP_PRIVATE_KEY` - GitHub App private key (PEM format)

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
      gh_app_id: ${{ secrets.GH_APP_ID }}
      gh_app_private_key: ${{ secrets.GH_APP_PRIVATE_KEY }}
```

### Required Secrets

- `GITHUB_TOKEN` - Automatically available; used for PR creation
- `GH_APP_ID` - GitHub App numeric ID (for private repo access)
- `GH_APP_PRIVATE_KEY` - GitHub App private key, PEM format (for private repo access)

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
| Dispatch not received | Check `GH_APP_ID`/`GH_APP_PRIVATE_KEY` secrets and App installation |
| Unauthorized sender | Add sender to `allowed_senders` |
| No PR created | Verify `contents: write` permission |
| Script not found | Check `update_script_path` or use default |
| No commit log | Ensure GitHub App is installed on sender repo |
| Multiple PRs from same sender | Expected: only one PR per sender (updates automatically) |
| Force-push warnings | Expected behavior: PR branch updates with latest changes |

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

- [DISPATCH_SYSTEM.md](DISPATCH_SYSTEM.md) - Complete setup and usage guide
- [MERGE_ORDER_SAFETY.md](MERGE_ORDER_SAFETY.md) - How the system prevents wrong-order PR merging
