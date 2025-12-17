#!/usr/bin/env python3
"""
West manifest updater tool

Updates revision fields in west.yml manifest files based on repository identifier.
This tool is used by the dependency update automation to keep manifest files in sync.
"""
import sys
import yaml

def load_yaml(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to read {path}: {e}", file=sys.stderr)
        sys.exit(1)

def dump_yaml(data, path):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"Error: Failed to write {path}: {e}", file=sys.stderr)
        sys.exit(1)

def update_revision(manifest, repo_identifier, new_rev):
    changed = False
    old_rev = None
    projects = manifest.get('projects') or []
    
    # Extract the repo name from identifier (e.g., "lhasystems/zephyr_boards" -> "zephyr_boards")
    # This must exactly match a repo-path value in the manifest
    repo_name = repo_identifier.split('/')[-1]
    
    for p in projects:
        repo_path = p.get('repo-path', '')
        
        # Match only by repo-path (exact match required)
        if repo_path == repo_name:
            old_rev = p.get('revision')
            if old_rev != new_rev:
                p['revision'] = new_rev
                changed = True
            break  # repo-path values are unique, no need to continue
    
    return changed, old_rev

def main():
    if len(sys.argv) != 4:
        print("usage: update_west.py <west.yml path> <repo-identifier> <new-revision>", file=sys.stderr)
        sys.exit(2)
    path, repo_identifier, new_rev = sys.argv[1], sys.argv[2], sys.argv[3]
    data = load_yaml(path)
    changed = False
    old_rev = None
    if isinstance(data, dict) and 'manifest' in data and isinstance(data['manifest'], dict):
        changed, old_rev = update_revision(data['manifest'], repo_identifier, new_rev)
    else:
        changed, old_rev = update_revision(data, repo_identifier, new_rev)
    if changed:
        dump_yaml(data, path)
        print("status=updated")
        if old_rev:
            print(f"old_revision={old_rev}")
        sys.exit(0)
    else:
        print("status=no-change")
        sys.exit(0)

if __name__ == "__main__":
    main()
