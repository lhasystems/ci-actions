# Dependency Update Dispatch System

This repository contains reusable GitHub Actions workflows and tools for managing dependency updates across multiple repositories using the repository_dispatch mechanism.

## Overview

The dispatch system automates dependency tracking and updates across the lhasystems organization repositories. When a source repository (like `c_lib_control` or `zephyr_boards`) changes, it automatically notifies dependent repositories (like `ec_diffuser`), which can then create pull requests to update their manifest files.

## System Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Source Repo    │         │  Source Repo    │
│  c_lib_control  │         │ zephyr_boards   │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │ dispatch-dependency-update.yml
         │ (notifies on changes)    │
         └──────────┬────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Target Repo         │
         │  ec_diffuser         │
         │                      │
         │  handle-dependency-  │
         │  update.yml          │
         │  (receives & PRs)    │
         └──────────────────────┘
```

## Components

### 1. Reusable Workflows

#### `dispatch-dependency-update.yml`

A reusable workflow that sends repository_dispatch events to dependent repositories when changes are made.

**Use Case:** Called by source repositories (c_lib_control, zephyr_boards) when their dependencies change.

**Inputs:**
- `target_repos` (required): Comma-separated list of target repository names (e.g., "ec_diffuser,other_repo")
- `event_type` (optional): The repository_dispatch event type (default: "dependency_update_request")

**Secrets:**
- `gh_app_id` (required): GitHub App ID for creating an installation token
- `gh_app_private_key` (required): GitHub App private key for creating an installation token

**Example Usage in Source Repository:**

```yaml
name: Notify dependent repositories

on:
  push:
    paths:
      - 'src/**'
      - 'include/**'
      - 'Kconfig'
      - 'CMakeLists.txt'
  workflow_dispatch:

jobs:
  notify:
    uses: lhasystems/ci-actions/.github/workflows/dispatch-dependency-update.yml@main
    with:
      target_repos: 'ec_diffuser,other_dependent_repo'
    secrets:
      gh_app_id: ${{ secrets.GH_APP_ID }}
      gh_app_private_key: ${{ secrets.GH_APP_PRIVATE_KEY }}
```

#### `handle-dependency-update.yml`

A reusable workflow that handles repository_dispatch events, updates manifest files, and creates pull requests.

**Use Case:** Called by target repositories (ec_diffuser) when they receive dependency update notifications.

**Inputs:**
- `allowed_senders` (required): Comma-separated list of allowed sender repositories (e.g., "lhasystems/c_lib_control,lhasystems/zephyr_boards")
- `manifest_path` (optional): Path to the west.yml or manifest file (default: "west.yml")
- `update_script_path` (optional): Path to update script (default: downloads from ci-actions)

**Secrets:**
- `gh_token` (required): GitHub token for creating PRs (GITHUB_TOKEN is sufficient)
- `gh_app_id` (required): GitHub App ID for creating an installation token (used for private repo access)
- `gh_app_private_key` (required): GitHub App private key (used for private repo access)

**Example Usage in Target Repository:**

```yaml
name: Handle dependency updates

on:
  repository_dispatch:
    types: [dependency_update_request]

jobs:
  update:
    uses: lhasystems/ci-actions/.github/workflows/handle-dependency-update.yml@main
    with:
      allowed_senders: 'lhasystems/c_lib_control,lhasystems/zephyr_boards'
      manifest_path: 'west.yml'
    secrets:
      gh_token: ${{ secrets.GITHUB_TOKEN }}
      gh_app_id: ${{ secrets.GH_APP_ID }}
      gh_app_private_key: ${{ secrets.GH_APP_PRIVATE_KEY }}
```

### 2. Tools

#### `tools/update_west.py`

Python script for updating revision fields in west.yml manifest files.

**Usage:**
```bash
python3 update_west.py <west.yml path> <repo-identifier> <new-revision>
```

**Example:**
```bash
python3 tools/update_west.py west.yml lhasystems/c_lib_control abc1234567890def
```

**Output:**
- Prints `status=updated` and `old_revision=<sha>` on successful update
- Prints `status=no-change` if revision is already current
- Exits with code 0 on success, non-zero on error

## Setup Instructions

### For Source Repositories (Senders)

1. **Create workflow file** (e.g., `.github/workflows/notify-dependencies.yml`):
   ```yaml
   name: Notify dependent repositories

   on:
     push:
       paths:
         - 'src/**'
         - 'include/**'
         # Add paths that should trigger notifications
     workflow_dispatch:

   jobs:
     notify:
       uses: lhasystems/ci-actions/.github/workflows/dispatch-dependency-update.yml@main
       with:
         target_repos: 'ec_diffuser'  # Add target repos
       secrets:
         gh_app_id: ${{ secrets.GH_APP_ID }}
         gh_app_private_key: ${{ secrets.GH_APP_PRIVATE_KEY }}
   ```

2. **Configure secrets:**
   - Go to repository Settings → Secrets and variables → Actions
   - Create secret `GH_APP_ID` with your GitHub App's numeric ID
   - Create secret `GH_APP_PRIVATE_KEY` with your GitHub App's private key (PEM format)
   - The GitHub App must be installed on all target repositories

### For Target Repositories (Receivers)

1. **Create workflow file** (e.g., `.github/workflows/dependency-updates.yml`):
   ```yaml
   name: Handle dependency updates

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
         allowed_senders: 'lhasystems/c_lib_control,lhasystems/zephyr_boards'
         manifest_path: 'west.yml'
       secrets:
         gh_token: ${{ secrets.GITHUB_TOKEN }}
         gh_app_id: ${{ secrets.GH_APP_ID }}
         gh_app_private_key: ${{ secrets.GH_APP_PRIVATE_KEY }}
   ```

2. **Configure secrets:**
   - `GITHUB_TOKEN` is automatically available — no setup needed for PR creation
   - Create `GH_APP_ID` with your GitHub App's numeric ID
   - Create `GH_APP_PRIVATE_KEY` with your GitHub App's private key (PEM format)
   - The GitHub App must be installed on this repository and on all sender repositories (for commit log access)

## Workflow Details

### Sender Workflow Process

1. **Trigger:** Push to watched paths or manual trigger
2. **Find Commit:** Uses the triggering commit (GITHUB_SHA)
3. **Dispatch:** Sends repository_dispatch event to each target repo with:
   - Commit SHA
   - Sender repository name
   - Branch name

### Receiver Workflow Process

1. **Validate:** Checks that sender is in allowed list
2. **Update:** Uses `update_west.py` to update manifest file
3. **Changelog:** Fetches commit log between old and new revisions using the GitHub App token
4. **Create PR:** Opens pull request with changes and commit log

## Configuration

### Adding More Target Repositories

In the sender repository workflow, add to the `target_repos` input:
```yaml
with:
  target_repos: 'ec_diffuser,new_repo,another_repo'
```

### Changing Watched Paths

The reusable workflow uses the triggering commit (`GITHUB_SHA`), so only the trigger paths need updating in your repository workflow:
```yaml
on:
  push:
    paths:
      - 'src/**'
      - 'include/**'
      - 'west.yml'
```

### Allowing Additional Senders

In the receiver repository workflow, add to the `allowed_senders` input:
```yaml
with:
  allowed_senders: 'lhasystems/c_lib_control,lhasystems/zephyr_boards,lhasystems/new_sender'
```

### Selective Updates (Manual Override)

The single-branch-per-sender strategy always provides the **latest** update. If you need to apply only specific updates:

1. **Close the auto-generated PR** without merging
2. **Manually update** `west.yml` to the desired commit
3. **Create a manual PR** with your selected revision
4. **Merge the manual PR**

The next auto-update will continue from your manually selected commit. See [MERGE_ORDER_SAFETY.md](MERGE_ORDER_SAFETY.md#selective-updates-what-if-you-want-to-skip-an-update) for detailed procedures.

## Security Considerations

### Token Permissions

- **`GITHUB_TOKEN`:** Default token is sufficient for creating PRs in the same repository (used by `handle-dependency-update.yml`)
- **GitHub App:** Provides short-lived installation tokens via `actions/create-github-app-token@v1`; used for git authentication and fetching commit logs from private repositories. The App is read-only for repository contents and must be installed on all sender repositories.
- **`GH_APP_ID`:** The numeric App ID found in your GitHub App settings
- **`GH_APP_PRIVATE_KEY`:** The PEM-format private key generated in your GitHub App settings

### Sender Validation

The receiver workflow validates that dispatches come from allowed senders. Any repository not in the `allowed_senders` list will be rejected.

## Troubleshooting

### Dispatch Not Received

**Symptoms:** Target repository workflow doesn't trigger

**Solutions:**
1. Verify `GH_APP_ID` and `GH_APP_PRIVATE_KEY` secrets are set correctly
2. Confirm the GitHub App is installed on all target repositories
3. Ensure receiver workflow file is on default branch
4. Verify receiver workflow listens for correct event type

### PR Creation Fails

**Symptoms:** Receiver workflow runs but doesn't create PR

**Solutions:**
1. Check `contents: write` and `pull-requests: write` permissions are set
2. Verify there are actual changes to commit
3. Check workflow logs for error messages

### Unauthorized Sender

**Symptoms:** Receiver workflow fails with "Sender not authorized"

**Solutions:**
1. Add sender repository to `allowed_senders` input
2. Ensure sender uses full repository path (e.g., "lhasystems/c_lib_control")

### No Commit Log in PR

**Symptoms:** PR body shows "No commit log available"

**Solutions:**
1. Confirm the GitHub App is installed on the sender repository
2. Verify the App has `contents: read` permission on the sender repository
3. Check workflow logs for API error messages

### Update Script Fails

**Symptoms:** "Error: Failed to read west.yml" or similar

**Solutions:**
1. Verify `manifest_path` input points to correct file
2. Check west.yml has valid YAML syntax
3. Ensure repo-path in manifest matches repository name

### Force-Push Warnings on PR Branch

**Symptoms:** GitHub shows force-push warnings on auto-update branches

**Solutions:**
This is **expected behavior**. The system intentionally force-pushes to keep the PR current with the latest changes from the sender. This is a feature, not a bug, that prevents merge order issues.

### Multiple PRs from Same Sender

**Symptoms:** Multiple open PRs exist for the same sender repository

**Solutions:**
This should not happen with the current implementation. If you see this:
1. Verify you're using the latest version of `handle-dependency-update.yml`
2. Check that all PRs are using the same branch name pattern `auto/update-{sender}`
3. Manually close older PRs if they exist from previous versions

## Testing

### Manual Dispatch

Test the sender workflow:
```bash
# In source repository
gh workflow run notify-dependencies.yml
```

### Test Update Script Locally

```bash
# Clone ci-actions
git clone https://github.com/lhasystems/ci-actions.git

# Test update
python3 ci-actions/tools/update_west.py west.yml lhasystems/c_lib_control <commit-sha>

# Check changes
git diff west.yml
```

### Simulate Dispatch

```bash
# Send manual repository_dispatch event
gh api repos/lhasystems/ec_diffuser/dispatches \
  -X POST \
  -f event_type=dependency_update_request \
  -F client_payload[commit]=abc123 \
  -F client_payload[sender]=lhasystems/c_lib_control \
  -F client_payload[branch]=main
```

## Migration Guide

### Migrating from Repository-Specific Workflows

If you have existing dispatch workflows in your repositories:

1. **In Source Repository:**
   - Replace workflow content with call to `dispatch-dependency-update.yml`
   - Move configuration to workflow inputs
   - Keep your existing trigger conditions

2. **In Target Repository:**
   - Replace workflow content with call to `handle-dependency-update.yml`
   - Move allowed senders to workflow inputs
   - Remove update script (uses centralized version)

3. **Update Documentation:**
   - Reference this central documentation
   - Remove repository-specific dispatch documentation

## Handling Multiple Updates

### Single-Branch-Per-Sender Strategy

To prevent issues with merging PRs in the wrong order, the system uses a **single branch per sender** approach:

- Each sender gets one consistent branch: `auto/update-{sender}`
- When a new update arrives from the same sender, it **force-pushes** to the existing branch
- This automatically updates the existing PR with the latest changes
- Only one PR per sender exists at any time, eliminating merge order concerns

**Example Scenario:**
1. `c_lib_control` pushes commit `abc123` → PR created on branch `auto/update-lhasystems/c_lib_control`
2. `c_lib_control` pushes commit `def456` → Same branch is force-pushed, PR is updated
3. You only see one PR that always points to the latest commit

**Benefits:**
- ✅ Impossible to merge in wrong order (only one PR exists)
- ✅ No accumulation of stale PRs
- ✅ PR automatically stays current with latest changes
- ✅ Simple and maintainable

**Considerations:**
- Force-pushes to the branch are expected behavior
- Each update includes a complete commit log from previous to current revision
- The PR description shows the current commit hash

## Best Practices

1. **Limit Watched Paths:** Only watch paths that truly affect dependencies
2. **Use Specific Paths:** Avoid watching entire directories unless necessary
3. **Validate Changes:** Review auto-generated PRs before merging
4. **Monitor Failures:** Set up notifications for workflow failures
5. **Version Pinning:** Consider pinning workflow versions (e.g., `@v1` instead of `@main`)
6. **Rapid Updates:** The system handles rapid successive updates gracefully by updating the same PR

## References

- [GitHub Repository Dispatch Documentation](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)
- [Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [West Manifest Format](https://docs.zephyrproject.org/latest/develop/west/manifest.html)

## Changelog

### GitHub App Token Migration
- Replaced static PAT secrets (`dispatch_token`, `gh_token`, `private_repo_token`) with GitHub App token authentication
- Both workflows now use `actions/create-github-app-token@v1` to generate short-lived installation tokens
- Required secrets are now unified: `gh_app_id` and `gh_app_private_key` for both sender and receiver

### Initial Release
- Extracted from c_lib_control, zephyr_boards, and ec_diffuser repositories
- Created reusable workflows for dispatch sender and receiver
- Centralized update_west.py tool
- Comprehensive documentation

## Support

For issues or questions:
1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Open an issue in the ci-actions repository
