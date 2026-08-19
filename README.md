# ci-actions

Reusable GitHub Actions workflows and tools for the lhasystems organization.

## Contents

- **Reusable Workflows** - Shared workflows for common CI/CD patterns
- **Tools** - Scripts and utilities for automation
- **Documentation** - Setup guides and best practices

## Features

### Dependency Update Dispatch System

Automated dependency tracking and updates across repositories using GitHub's repository_dispatch mechanism.

- **Sender Workflow:** Notifies dependent repositories when source code changes
- **Receiver Workflow:** Handles notifications and creates update PRs automatically
- **Update Tool:** Python script for updating west.yml manifest files
- **Merge Order Safety:** Single-branch-per-sender strategy prevents PRs from being merged in wrong order

📖 **[Full Documentation](DISPATCH_SYSTEM.md)**

#### Quick Start

**In Source Repository (sends updates):**
```yaml
jobs:
  notify:
    uses: lhasystems/ci-actions/.github/workflows/dispatch-dependency-update.yml@main
    with:
      target_repos: 'ec_diffuser'
    secrets:
      gh_app_id: ${{ secrets.GH_APP_ID }}
      gh_app_private_key: ${{ secrets.GH_APP_PRIVATE_KEY }}
```

**In Target Repository (receives updates):**
```yaml
jobs:
  update:
    uses: lhasystems/ci-actions/.github/workflows/handle-dependency-update.yml@main
    with:
      allowed_senders: 'lhasystems/c_lib_control,lhasystems/zephyr_boards'
    secrets:
      gh_token: ${{ secrets.GITHUB_TOKEN }}
      gh_app_id: ${{ secrets.GH_APP_ID }}
      gh_app_private_key: ${{ secrets.GH_APP_PRIVATE_KEY }}
```

### Package Publishing

Publishes a Node package to GitHub Packages and records the release as a git tag and a GitHub
Release, so every published version points at the commit it was built from.

- **Version-bump driven:** the version in `package.json` decides when a release happens
- **Fails without a bump:** a push whose version is not newer than the published one fails the run
- **Tags and releases:** creates `v<version>` and a GitHub Release with generated notes after a
  successful publish

```yaml
jobs:
  publish:
    uses: lhasystems/ci-actions/.github/workflows/publish-npm-package.yml@main
    permissions:
      contents: write
      packages: write
```

## Documentation

- **[Quick Reference](QUICK_REFERENCE.md)** - Fast lookup for common tasks
- **[Full Documentation](DISPATCH_SYSTEM.md)** - Comprehensive guide and setup
- **[Merge Order Safety](MERGE_ORDER_SAFETY.md)** - How the system prevents wrong-order PR merging
- **[Architecture Diagrams](ARCHITECTURE.md)** - Visual system overview
- **[Extraction Summary](EXTRACTION_SUMMARY.md)** - What was extracted and migration path
- **[Examples](examples/)** - Sample workflow files for different repository types

## Available Workflows

### `dispatch-dependency-update.yml`

Sends repository_dispatch events to dependent repositories when source files change.

**Required inputs:**
- `target_repos`: Comma-separated target repository names

**Required secrets:**
- `gh_app_id`: GitHub App ID
- `gh_app_private_key`: GitHub App private key

### `handle-dependency-update.yml`

Handles dependency update notifications, updates manifest files, and creates pull requests.

**Required inputs:**
- `allowed_senders`: Comma-separated list of authorized sender repositories

**Required secrets:**
- `gh_token`: Token for PR creation (GITHUB_TOKEN is sufficient)
- `gh_app_id`: GitHub App ID (for private repo access)
- `gh_app_private_key`: GitHub App private key (for private repo access)

### `publish-npm-package.yml`

Builds, tests and publishes a Node package to GitHub Packages, then tags the commit and creates a
GitHub Release. Intended to be called on pushes to the default branch.

The version in `package.json` is the release trigger. The workflow **fails** when that version is
not strictly newer than the latest version in the registry, or when the tag already exists, so
nothing reaches the default branch without a version bump.

**Inputs (all optional):**
- `node_version`: Node.js version (default `20`)
- `pnpm_version`: pnpm version (default `8`)
- `run_tests`: run `pnpm test` before publishing (default `true`)
- `tag_prefix`: prefix for the created tag (default `v`, so the tag is `v<version>`)
- `create_release`: create a GitHub Release with generated notes (default `true`)

**Required permissions on the calling job:**
- `contents: write` (push the tag, create the release)
- `packages: write` (publish to GitHub Packages)

No secrets to pass: `GITHUB_TOKEN` is available to the called workflow automatically.

## Tools

### `update_west.py`

Updates revision fields in west.yml manifest files based on repository identifier.

```bash
python3 tools/update_west.py <manifest-path> <repo-identifier> <new-revision>
```

## Usage

To use these workflows in your repository:

1. Reference the workflow in your `.github/workflows` directory
2. Provide required inputs and secrets
3. Follow the setup instructions in [DISPATCH_SYSTEM.md](DISPATCH_SYSTEM.md)

## Contributing

When adding new workflows or tools:
1. Add comprehensive documentation
2. Include usage examples
3. Update this README

## License

See individual repositories for license information.
