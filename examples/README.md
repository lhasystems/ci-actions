# Example Workflows

This directory contains example workflow files showing how to use the reusable workflows from ci-actions.

## For Package Repositories

- **`publish-npm-package.yml`** - Publishes a Node package to GitHub Packages, tagged and released

## For Source Repositories (Senders)

Copy and adapt the example workflows based on your repository type:

- **`sender-c-lib.yml`** - For C libraries like c_lib_control
- **`sender-boards.yml`** - For board definitions like zephyr_boards

## For Target Repositories (Receivers)

Copy and adapt:

- **`receiver-application.yml`** - For application repositories like ec_diffuser

## Integration Steps

### Package Repository Setup

1. Copy `publish-npm-package.yml` to `.github/workflows/publish.yml`
2. Nothing to customize for the mlm-* packages - the defaults are Node 20 and pnpm 8, and the
   package name, version and tag come from `package.json`
3. Release by bumping `version` in `package.json` and merging to `main`; a push without a bump
   fails the run

### Source Repository Setup

1. Copy the appropriate sender example to `.github/workflows/notify-dependencies.yml`
2. Customize:
   - Update `target_repos` with repositories that depend on you
   - Adjust the `paths` triggers to match what should fire notifications
3. Add `GH_APP_ID` and `GH_APP_PRIVATE_KEY` secrets to repository settings

### Target Repository Setup

1. Copy `receiver-application.yml` to `.github/workflows/handle-dependency-updates.yml`
2. Customize:
   - Update `allowed_senders` with all your dependencies
   - Adjust `manifest_path` if not using west.yml
3. Add `GH_APP_ID` and `GH_APP_PRIVATE_KEY` secrets to repository settings (`GITHUB_TOKEN` is automatically available for PR creation)

## Testing

After setup:

1. **Test manually:**
   ```bash
   gh workflow run notify-dependencies.yml
   ```

2. **Verify in target:**
   - Check Actions tab for triggered workflow
   - Look for auto-generated PR

3. **Test with actual change:**
   - Make a change to a watched path
   - Push to default branch
   - Verify notification and PR creation
