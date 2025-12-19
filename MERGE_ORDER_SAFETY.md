# Merge Order Safety

## Problem Statement

When a source repository pushes multiple commits in rapid succession, the dispatch system could create multiple pull requests in the target repository. Without proper safeguards, these PRs could be merged in the wrong order, causing the manifest to point to an older commit instead of the latest one.

### Example Scenario (Without Safety Mechanism)

1. Developer pushes commit `A` to `c_lib_control`
2. Workflow creates PR #1 with branch `auto/update-lhasystems/c_lib_control-commitA`
3. Developer quickly pushes commit `B` to `c_lib_control`
4. Workflow creates PR #2 with branch `auto/update-lhasystems/c_lib_control-commitB`
5. Reviewer merges PR #2 first (manifest now points to commit `B`) ✅
6. Reviewer then merges PR #1 (manifest now points to commit `A`) ❌ **WRONG ORDER!**

Result: The manifest points to the older commit `A` instead of the newer commit `B`.

## Solution: Single-Branch-Per-Sender Strategy

The system prevents this problem by using a **consistent branch name per sender**, regardless of the commit being updated to.

### How It Works

- Each sender repository gets **one dedicated branch**: `auto/update-{sender}`
- When a new update arrives from the same sender, the workflow **force-pushes** to this branch
- The existing PR is automatically updated with the latest changes
- Only **one PR per sender** exists at any time

### Example Scenario (With Safety Mechanism)

1. Developer pushes commit `A` to `c_lib_control`
2. Workflow creates PR #1 with branch `auto/update-lhasystems/c_lib_control`
3. PR #1 shows: Update to commit `A`
4. Developer quickly pushes commit `B` to `c_lib_control`
5. Workflow force-pushes to the **same branch** `auto/update-lhasystems/c_lib_control`
6. PR #1 is automatically updated to show: Update to commit `B`
7. Only one PR exists, pointing to the latest commit ✅

Result: It's impossible to merge in the wrong order because there's only one PR to merge.

## Implementation Details

### Branch Naming

**Before (problematic):**
```
auto/update-lhasystems/c_lib_control-abc1234567890def
auto/update-lhasystems/c_lib_control-def4567890123abc
```
Multiple branches → Multiple PRs → Potential wrong order

**After (safe):**
```
auto/update-lhasystems/c_lib_control
```
Single branch → Single PR → Always latest

### PR Title and Description

The PR title and description are updated to reflect the current state:

**Title:**
```
ci: update lhasystems/c_lib_control (latest)
```

**Description:**
```
This PR updates west.yml to point the project lhasystems/c_lib_control to the latest commit.

Current commit: abc1234567890def
Branch: main

> Note: This PR uses a consistent branch name per sender. When new updates arrive 
> from the same sender, this PR will be automatically updated with the latest changes, 
> ensuring updates are always applied in the correct order.

## Changes
Updating from `def4567890123abc` to `abc1234567890def`

## Commit Log
- [abc1234] Fix critical bug
- [bcd2345] Add new feature
- [cde3456] Update documentation
```

### Workflow Behavior

The `peter-evans/create-pull-request` action handles the logic:

1. **First update:** Creates a new PR with the branch `auto/update-{sender}`
2. **Subsequent updates:** 
   - Detects existing PR with the same branch name
   - Force-pushes new commit to the branch
   - Updates PR description with latest information
   - Maintains PR number and conversation history

## Benefits

### 1. Prevents Wrong Order Merging
✅ **By Design:** Only one PR per sender can exist at any time
✅ **No Manual Intervention:** System automatically supersedes older updates
✅ **No Configuration:** Works out of the box

### 2. Reduces PR Clutter
✅ No accumulation of stale PRs
✅ No need to manually close outdated PRs
✅ Clean PR list with only current updates

### 3. Maintains Full Visibility
✅ Commit log shows all changes from previous to current revision
✅ PR description always shows current commit hash
✅ Git history on the branch shows the progression (if needed)

### 4. Handles Rapid Updates
✅ System gracefully handles multiple updates in quick succession
✅ Each update includes complete changelog from last merged revision
✅ No race conditions or conflicts

## Edge Cases and Considerations

### Multiple Senders

Each sender gets its own branch, so updates from different senders don't interfere:

```
auto/update-lhasystems/c_lib_control     → PR for c_lib_control
auto/update-lhasystems/zephyr_boards     → PR for zephyr_boards
auto/update-lhasystems/c_lib_mesh_vav    → PR for c_lib_mesh_vav
```

All can have open PRs simultaneously without issues.

### Force-Push Warnings

GitHub may show force-push indicators on the PR branch. This is **expected and correct behavior**. The force-push ensures the PR always reflects the latest changes.

### Merge Conflicts

If a PR has been open for a long time and the base branch has diverged:
1. The force-push will update the branch with the latest manifest changes
2. The `create-pull-request` action will rebase if needed
3. Manual resolution may be required in rare cases

### Review Process

Reviewers should understand:
- The PR may update while under review (if new commits arrive)
- This is a feature, not a bug
- The PR always shows the **latest** state from the sender
- Review and merge the current state shown in the PR

## Comparison with Alternative Approaches

### Alternative 1: Unique Branch Names (Original Approach)

❌ **Problem:** Multiple PRs accumulate, can be merged in wrong order
✅ **Benefit:** Clear history of each individual update attempt
📊 **Verdict:** Rejected due to merge order risk

### Alternative 2: Auto-Close Old PRs with Superseding

✅ **Benefit:** Clear audit trail of superseding
❌ **Problem:** More complex, leaves many closed PRs
❌ **Problem:** Requires additional API calls to search and close PRs
📊 **Verdict:** More complex than single-branch approach

### Alternative 3: Merge Order Validation with Status Checks

✅ **Benefit:** Prevents merging outdated PRs via checks
❌ **Problem:** Requires status check infrastructure
❌ **Problem:** Still accumulates PRs
❌ **Problem:** Doesn't prevent creating multiple PRs
📊 **Verdict:** Adds complexity without solving PR proliferation

### Alternative 4: Batching/Debouncing

✅ **Benefit:** Reduces frequency of PRs
❌ **Problem:** Adds delay to updates
❌ **Problem:** Complex to implement correctly
❌ **Problem:** May miss rapid changes if not configured properly
📊 **Verdict:** Unnecessary with single-branch approach

## Testing the Safety Mechanism

### Manual Test Procedure

1. **Setup:** Configure a source and target repository with the workflows
2. **Test rapid updates:**
   ```bash
   # In source repository
   git commit --allow-empty -m "Test commit 1"
   git push
   
   # Wait 5 seconds for dispatch
   
   git commit --allow-empty -m "Test commit 2"
   git push
   
   # Wait 5 seconds for dispatch
   
   git commit --allow-empty -m "Test commit 3"
   git push
   ```
3. **Verify:** Check target repository
   - Should see only **one open PR** for the sender
   - PR should show the latest commit (Test commit 3)
   - Check branch name is `auto/update-{sender}` without commit hash
   - PR description should indicate it's the "latest" update

### Expected Behavior

✅ Single PR exists per sender at any time
✅ PR updates automatically with each new dispatch
✅ PR always points to the latest commit
✅ Commit log shows all changes from last merged revision to current
✅ No stale PRs accumulate

## Migration from Previous Versions

If you're upgrading from a version that used unique branch names per commit:

### Cleanup Old PRs

1. Close any open PRs with old branch naming pattern:
   ```
   auto/update-{sender}-{commit-hash}
   ```
2. New PRs will use the correct pattern:
   ```
   auto/update-{sender}
   ```

### No Code Changes Required

The workflow update is backward compatible:
- Source repositories don't need any changes
- Target repositories automatically benefit from the new behavior
- Existing tokens and permissions work unchanged

## Summary

The single-branch-per-sender strategy is a simple, elegant solution that:

✅ **Prevents** wrong-order merging by design  
✅ **Simplifies** PR management (one PR per sender)  
✅ **Maintains** full visibility and audit trail  
✅ **Requires** no manual intervention  
✅ **Works** automatically with existing infrastructure  

This approach prioritizes correctness and simplicity over preserving every individual update attempt as a separate PR. The commit history in the PR description provides full visibility into what changed, making this the ideal solution for automated dependency updates.
