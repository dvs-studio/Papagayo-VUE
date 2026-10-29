#!/usr/bin/env python3
"""
Papagayo-NG Crucial Files Backup Packager
=========================================
Packs only crucial source code, documentation, rules, dictionaries, and configurations
strictly excluding media assets (audio, viseme bitmaps, icons, binary archives).

Guarantees the presence of:
  - AGENTIC_HANDOVER.md
  - API_KIT.md
at the root of the resulting zip archive.
"""

import os
import sys
import zipfile
from pathlib import Path

# Media extensions to strictly exclude
MEDIA_EXTENSIONS = {
    # Audio
    '.wav', '.mp3', '.ogg', '.flac', '.aiff', '.aif', '.m4a', '.aac', '.wma',
    # Images / Icons
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.ico', '.icns',
    '.hqx', '.tif', '.tiff', '.kra', '.psd', '.xcf',
    # Video
    '.mp4', '.avi', '.mov', '.mkv', '.webm'
}

# Directories to strictly exclude
EXCLUDED_DIR_NAMES = {
    '.git', '.github', '.aistudio', '__pycache__', 'node_modules',
    'venv', '.venv', 'build', 'dist', '.pytest_cache',
    'mouths', 'icons', 'papagayo-ng-upstream', 'assets'
}

# Explicit crucial root files
MANDATORY_HANDOVER_FILES = [
    'AGENTIC_HANDOVER.md',
    'API_KIT.md'
]

def is_crucial_file(rel_path: str) -> bool:
    """Check if file should be included in the crucial files backup."""
    p = Path(rel_path)
    parts = p.parts

    # Exclude unwanted directories
    for part in parts[:-1]:
        if part in EXCLUDED_DIR_NAMES:
            return False

    # Check extension
    suffix = p.suffix.lower()
    if suffix in MEDIA_EXTENSIONS:
        return False
    if suffix in {'.pyc', '.pyo', '.zip', '.tar', '.gz'}:
        return False

    # Allow specific directories
    if parts[0] in {'breakdowns', 'phonemes', 'translations', 'util', 'test'}:
        return True

    if parts[0] == 'rsrc':
        # Include dictionaries and language files, UI files, HTML files
        if len(parts) > 1 and parts[1] in {'languages', 'i18n'}:
            return True
        if suffix in {'.ui', '.html', '.txt', '.json'}:
            return True
        return False

    # Root level crucial files
    if len(parts) == 1:
        if suffix in {'.py', '.md', '.txt', '.json', '.yml', '.yaml', '.ts', '.qm', '.ui', '.qrc', '.spec', '.pro', '.nsi'}:
            return True
        if parts[0] in {'.gitignore', '_config.yml'}:
            return True

    return False

def create_backup(workspace_dir: str, output_zip_path: str) -> tuple[int, int]:
    """Creates the backup zip file containing only crucial files."""
    workspace = Path(workspace_dir).resolve()
    output_path = Path(output_zip_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Verify mandatory handover files exist in workspace
    for required in MANDATORY_HANDOVER_FILES:
        req_file = workspace / required
        if not req_file.is_file():
            raise FileNotFoundError(f"Mandatory file missing from workspace: {required}")

    included_files = []

    for root, dirs, files in os.walk(workspace):
        # Prune excluded directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES]

        for file in files:
            full_path = Path(root) / file
            try:
                rel_path = full_path.relative_to(workspace).as_posix()
            except ValueError:
                continue

            # Don't include the destination zip itself
            if full_path == output_path:
                continue

            if is_crucial_file(rel_path):
                included_files.append((full_path, rel_path))

    # Build zip file
    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for full_path, rel_path in sorted(included_files, key=lambda x: x[1]):
            zf.write(full_path, arcname=rel_path)

    # Audit archive contents
    with zipfile.ZipFile(output_path, 'r') as zf:
        namelist = zf.namelist()
        
        # Verify mandatory files
        for req in MANDATORY_HANDOVER_FILES:
            if req not in namelist:
                raise ValueError(f"Integrity check failed: {req} not found in zip archive!")

        # Verify no media files slipped in
        for name in namelist:
            ext = Path(name).suffix.lower()
            if ext in MEDIA_EXTENSIONS:
                raise ValueError(f"Integrity check failed: Media file leaked into backup: {name}")

    zip_size = output_path.stat().st_size
    return len(included_files), zip_size

if __name__ == '__main__':
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    out_zip = os.path.join(root_dir, 'papagayo-ng-core-backup.zip')
    if len(sys.argv) > 1:
        out_zip = sys.argv[1]

    print(f"Generating crucial files backup to: {out_zip}")
    file_count, byte_size = create_backup(root_dir, out_zip)
    print(f"SUCCESS: Packaged {file_count} crucial files ({byte_size / 1024:.1f} KB).")
    print(f"Strict exclusion of media files verified: 0 media assets present.")
    print(f"Mandatory files verified in root:")
    for f in MANDATORY_HANDOVER_FILES:
        print(f"  [x] {f}")
