# System Architecture Diagrams

Visual representations of the dispatch dependency update system.

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ci-actions Repository                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Reusable Workflows                                       │  │
│  │  • dispatch-dependency-update.yml (sender)                │  │
│  │  • handle-dependency-update.yml (receiver)                │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Tools                                                    │  │
│  │  • update_west.py                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                    ▲                           ▲
                    │ uses                      │ uses
                    │                           │
    ┌───────────────┴─────────┐    ┌──────────┴────────────┐
    │                         │    │                       │
┌───────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ c_lib_control │      │ zephyr_boards   │      │   ec_diffuser   │
│               │      │                 │      │                 │
│ [SENDER]      │      │ [SENDER]        │      │ [RECEIVER]      │
│               │      │                 │      │                 │
│ Monitors:     │      │ Monitors:       │      │ Receives:       │
│ • src/        │      │ • boards/       │      │ • Updates       │
│ • include/    │      │                 │      │ • Creates PR    │
│ • Kconfig     │      │                 │      │                 │
└───────┬───────┘      └────────┬────────┘      └─────────────────┘
        │                       │                        ▲
        │                       │                        │
        └───────────────┬───────┴────────────────────────┘
                        │ repository_dispatch
                        │ (dependency_update_request)
                        │
                        ▼
```

## Detailed Flow: Sender Side

```
┌──────────────────────────────────────────────────────────────┐
│ Source Repository (e.g., c_lib_control)                      │
└──────────────────────────────────────────────────────────────┘
                        │
                        │ Developer pushes changes to src/
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ GitHub Actions: Trigger on push                              │
│                                                              │
│ on:                                                          │
│   push:                                                      │
│     paths: ['src/**', 'include/**']                          │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Call Reusable Workflow                                       │
│                                                              │
│ uses: lhasystems/ci-actions/.github/workflows/              │
│       dispatch-dependency-update.yml@main                    │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 1: Checkout                                             │
│ • Fetch full git history                                     │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 2: Determine Commit                                     │
│ • Use triggering commit (GITHUB_SHA)                         │
│ • Extract commit SHA and short SHA                           │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 3: Send Dispatch (Matrix)                               │
│                                                              │
│ For each target_repo in [ec_diffuser, other_repo]:          │
│   • Create JSON payload:                                     │
│     {                                                        │
│       commit: "abc123...",                                   │
│       sender: "lhasystems/c_lib_control",                    │
│       branch: "main"                                         │
│     }                                                        │
│   • POST to GitHub API:                                      │
│     /repos/lhasystems/{target_repo}/dispatches               │
│   • Verify HTTP 204 response                                 │
└──────────────────────────────────────────────────────────────┘
```

## Detailed Flow: Receiver Side

```
┌──────────────────────────────────────────────────────────────┐
│ Target Repository (e.g., ec_diffuser)                        │
└──────────────────────────────────────────────────────────────┘
                        │
                        │ Receives repository_dispatch event
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ GitHub Actions: Trigger on repository_dispatch               │
│                                                              │
│ on:                                                          │
│   repository_dispatch:                                       │
│     types: [dependency_update_request]                       │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Call Reusable Workflow                                       │
│                                                              │
│ uses: lhasystems/ci-actions/.github/workflows/              │
│       handle-dependency-update.yml@main                      │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 1: Checkout                                             │
│ • Fetch repository with full history                         │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 2: Validate Sender                                      │
│ • Extract sender from payload                                │
│ • Check against allowed_senders list                         │
│ • Extract commit, branch info                                │
│ • ✓ Authorized / ✗ Reject                                    │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 3: Download Update Script (if remote)                   │
│ • curl update_west.py from ci-actions                        │
│ • Make executable                                            │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 4: Update Manifest                                      │
│ • Run: python3 update_west.py west.yml                       │
│         lhasystems/c_lib_control abc123...                   │
│ • Parse old_revision from output                             │
│ • Show git diff of changes                                   │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 5: Fetch Commit Log (optional)                          │
│ • If PRIVATE_REPO_TOKEN available:                           │
│   • Use gh CLI to fetch commit range                         │
│   • Format as markdown list with links                       │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 6: Create/Update Pull Request                           │
│ • Branch: auto/update-{sender} (consistent per sender)       │
│ • Title: ci: update {sender} (latest)                        │
│ • Body: Includes current commit, commit log, and details     │
│ • Labels: automated, ci                                      │
│ • Auto-delete branch after merge                             │
│ • Force-pushes to same branch if PR already exists           │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│ Result: Pull Request Created/Updated                         │
│                                                              │
│ • Only one PR per sender exists at any time                  │
│ • New updates from same sender update the existing PR        │
│ • Prevents merge order issues by design                      │
│ Developer reviews and merges PR                              │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────────────┐
│  Push to main   │
│  (src/file.c)   │
└────────┬────────┘
         │
         │ git log -n 1 -- src/
         ▼
┌─────────────────────────────────┐
│  Commit SHA: abc1234567890def   │
└────────┬────────────────────────┘
         │
         │ Create payload
         ▼
┌──────────────────────────────────────────┐
│  Payload:                                │
│  {                                       │
│    "commit": "abc1234567890def",         │
│    "sender": "lhasystems/c_lib_control", │
│    "branch": "main"                      │
│  }                                       │
└────────┬─────────────────────────────────┘
         │
         │ POST via GitHub API
         ▼
┌──────────────────────────────────────────┐
│  repository_dispatch event               │
│  type: dependency_update_request         │
│  client_payload: { ... }                 │
└────────┬─────────────────────────────────┘
         │
         │ Validate sender
         ▼
┌──────────────────────────────────────────┐
│  Is "lhasystems/c_lib_control"           │
│  in allowed_senders?                     │
│  ✓ Yes → Continue                        │
└────────┬─────────────────────────────────┘
         │
         │ Update manifest
         ▼
┌──────────────────────────────────────────┐
│  west.yml:                               │
│                                          │
│  - repo-path: c_lib_control              │
│    revision: def0987654321abc ← OLD      │
│    revision: abc1234567890def ← NEW      │
└────────┬─────────────────────────────────┘
         │
         │ Fetch commits
         ▼
┌──────────────────────────────────────────┐
│  Commit log: def0987...abc1234           │
│  - [abc1234] Fix bug in controller       │
│  - [bcd2345] Add new feature             │
│  - [cde3456] Update documentation        │
└────────┬─────────────────────────────────┘
         │
         │ Create PR
         ▼
┌──────────────────────────────────────────┐
│  Pull Request #123                       │
│  ci: update c_lib_control to abc1234     │
│                                          │
│  Updates west.yml with latest changes    │
│  Commit log included in description      │
└──────────────────────────────────────────┘
```

## Multi-Repository Example

```
┌───────────────┐
│c_lib_control  │────┐
│ (sender)      │    │
└───────────────┘    │
                     │
┌───────────────┐    │   ┌─────────────┐     ┌───────────────┐
│zephyr_boards  │────┼───│ ci-actions  │─────│ ec_diffuser   │
│ (sender)      │    │   │  (central)  │     │  (receiver)   │
└───────────────┘    │   └─────────────┘     └───────────────┘
                     │
┌───────────────┐    │
│c_lib_mesh_vav │────┘
│ (sender)      │
└───────────────┘

Each sender notifies ec_diffuser independently
ec_diffuser validates each sender and creates separate PRs
```

## Error Handling Flow

```
┌────────────────┐
│ Dispatch sent  │
└───────┬────────┘
        │
        ▼
   ┌─────────┐ HTTP 204
   │Success? ├─────────► Continue
   └────┬────┘
        │ HTTP 4xx/5xx
        ▼
   ┌─────────────┐
   │ Log error   │
   │ Exit 1      │
   └─────────────┘

┌──────────────────┐
│ Receive dispatch │
└────────┬─────────┘
         │
         ▼
   ┌──────────────┐ Yes
   │ Authorized?  ├─────────► Continue
   └────┬─────────┘
        │ No
        ▼
   ┌─────────────────┐
   │ Reject sender   │
   │ Log unauthorized│
   │ Exit 1          │
   └─────────────────┘

┌──────────────┐
│ Update file  │
└──────┬───────┘
       │
       ▼
   ┌──────────┐ Yes
   │ Changed? ├─────────► Create PR
   └────┬─────┘
        │ No
        ▼
   ┌──────────────┐
   │ No PR needed │
   │ Exit 0       │
   └──────────────┘
```

## Sequence Diagram

```
Developer    Source Repo    ci-actions    Target Repo    GitHub API
    │            │              │              │              │
    │──Push──────►│              │              │              │
    │            │              │              │              │
    │            │◄─Trigger─────┤              │              │
    │            │  workflow    │              │              │
    │            │              │              │              │
    │            │──Use─────────►│              │              │
    │            │  workflow    │              │              │
    │            │              │              │              │
    │            │              │──Find────────┤              │
    │            │              │  commit      │              │
    │            │              │              │              │
    │            │              │──Dispatch────┼──────────────►│
    │            │              │  event       │              │
    │            │              │              │              │
    │            │              │              │◄─Trigger─────┤
    │            │              │              │  workflow    │
    │            │              │              │              │
    │            │              │◄─Use─────────┤              │
    │            │              │  workflow    │              │
    │            │              │              │              │
    │            │              │──Validate────┤              │
    │            │              │  sender      │              │
    │            │              │              │              │
    │            │              │──Update──────┤              │
    │            │              │  manifest    │              │
    │            │              │              │              │
    │            │              │              │──Create PR───►│
    │            │              │              │              │
    │◄──Notify───┼──────────────┼──────────────┤              │
    │  PR ready  │              │              │              │
```
