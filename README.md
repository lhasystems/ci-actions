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
      dispatch_token: ${{ secrets.DISPATCH_TOKEN }}
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
```

## Documentation

- **[Quick Reference](QUICK_REFERENCE.md)** - Fast lookup for common tasks
- **[Full Documentation](DISPATCH_SYSTEM.md)** - Comprehensive guide and setup
- **[Architecture Diagrams](ARCHITECTURE.md)** - Visual system overview
- **[Extraction Summary](EXTRACTION_SUMMARY.md)** - What was extracted and migration path
- **[Examples](examples/)** - Sample workflow files for different repository types

## Available Workflows

### `dispatch-dependency-update.yml`

Sends repository_dispatch events to dependent repositories when source files change.

**Required inputs:**
- `target_repos`: Comma-separated target repository names

**Required secrets:**
- `dispatch_token`: GitHub token with repo scope

### `handle-dependency-update.yml`

Handles dependency update notifications, updates manifest files, and creates pull requests.

**Required inputs:**
- `allowed_senders`: Comma-separated list of authorized sender repositories

**Required secrets:**
- `gh_token`: Token for PR creation

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
