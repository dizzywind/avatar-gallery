#!/usr/bin/env python3
"""
Deploy new images from /data/hermes/media/images/ to the avatar gallery repo.
- Copies new images to repo images/ directory
- Updates data.json with new entries (theme = 'uncategorized' or detected from filename)
- Commits and pushes to master
- GitHub Pages auto-deploys on push
"""

import fcntl
import logging
import os
import json
import shutil
import subprocess
import re
import time
import errno
import sys
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("deploy-images")

LOCK_PATH = "/tmp/deploy-images.lock"

MEDIA_DIR = "/data/hermes/media/images"
IDLE_DIR = "/root/avatar-gallery/images"
REPO_DIR = "/root/avatar-gallery"
IMAGES_DIR = os.path.join(REPO_DIR, "images")
DATA_FILE = os.path.join(REPO_DIR, "data.json")

# Themes to detect from filename patterns
THEME_PATTERNS = {
    "lotus": ["lotus"],
    "fantasy": ["dragon", "elf", "wizard", "phoenix", "portal", "rune", "enchant", "magic", "fairy", "knight", "castle", "sword", "potion", "spell", "mythical", "unicorn", "griffin", "mermaid"],
    "scifi": ["cyber", "robot", "space", "astronaut", "neon", "chrome", "alien", "ship", "star", "galaxy", "future", "tech", "digital", "matrix", "android", "mech", "laser", "quantum", "hologram", "vr", "virtual"],
    "nature": ["mountain", "lake", "forest", "ocean", "flower", "tree", "wolf", "butterfly", "sunset", "sunrise", "field", "river", "waterfall", "garden", "leaf", "animal", "bird", "deer", "bear", "eagle", "coral", "reef", "underwater", "aurora", "northern"],
    "abstract": ["abstract", "fractal", "geometric", "fluid", "marble", "gradient", "pattern", "texture", "swirl", "glitch", "neon", "color", "shape", "wave", "spiral", "mandala", "sacred_geometry"],
    "mythology": ["divine", "providence", "yggdrasil", "ankh", "egyptian", "norse", "greek", "god", "goddess", "temple", "sacred", "holy", "spirit", "cosmic", "celestial", "ethereal", "mystic", "occult", "ritual", "ceremony"],
    "tattoo": ["tattoo", "ink", "brush", "sumi", "sumie", "woodblock", "ukiyo"],
    "watercolor": ["watercolor", "watercolour", "wash", "paint"],
    "minimalist": ["minimal", "minimalist", "line", "simple", "clean", "single", "continuous"],
}

def run_with_retry(cmd, **kwargs):
    """Run a subprocess command, retrying on transient fork/resource errors."""
    max_attempts = kwargs.pop('max_attempts', 3)
    base_delay = kwargs.pop('retry_delay', 1)
    for attempt in range(1, max_attempts + 1):
        try:
            result = subprocess.run(cmd, **kwargs)
            return result
        except (BlockingIOError, OSError) as e:
            if getattr(e, 'errno', None) in (errno.EAGAIN, errno.ENOMEM, 11):
                if attempt == max_attempts:
                    log.error("Command failed after %d attempts: %s", attempt, cmd)
                    raise
                delay = base_delay * (2 ** (attempt - 1))
                log.warning("Retry %d/%d for %s after %s in %.1fs", attempt, max_attempts, cmd, e, delay)
                time.sleep(delay)
                continue
            raise

def detect_theme(filename):
    """Detect theme from filename keywords."""
    fn_lower = filename.lower().replace("_", " ").replace("-", " ")
    
    # Check each theme's keywords
    for theme, keywords in THEME_PATTERNS.items():
        for kw in keywords:
            if kw in fn_lower:
                return theme
    
    return "uncategorized"

def get_repo_images():
    """Get set of image filenames already in the repo."""
    if not os.path.exists(IMAGES_DIR):
        return set()
    return set(f for f in os.listdir(IMAGES_DIR) if f.endswith(('.jpg', '.jpeg', '.png', '.webp')))

def get_media_images():
    """Get dict of {filename: full_path} from media/idle and avatar media directories."""
    dirs = [IDLE_DIR, MEDIA_DIR] if IDLE_DIR != MEDIA_DIR else [MEDIA_DIR]
    out = {}
    for d in dirs:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if f.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                out[f] = os.path.join(d, f)
    return out

def load_data():
    """Load data.json."""
    if not os.path.exists(DATA_FILE):
        return {"avatars": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    """Save data.json."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_id(filename, theme):
    """Generate a unique ID for the avatar entry."""
    base = re.sub(r"[_\s]+", "_", filename.rsplit(".", 1)[0].lower())
    base = re.sub(r"[^a-z0-9_]", "", base)
    if len(base) > 40:
        base = base[:40]
    return f"{theme}_{base}"

def reconcile_corrupt_entries(avatars):
    """Normalize corrupt state-blob entries while preserving legacy metadata."""
    normalized = []
    corrupt_count = 0
    for a in avatars:
        if isinstance(a, dict) and not a.get("filename"):
            corrupt_count += 1
            prompt = (a.get("prompt") or "").strip()
            theme = (a.get("theme") or "").strip() or "uncategorized"
            a["prompt"] = prompt
            a["theme"] = theme
            if not a.get("id"):
                a["id"] = f"uncategorized_corrupt_{corrupt_count}"
            if (a.get("category") or "").strip():
                a["category"] = a["category"].strip()
            else:
                a["category"] = theme
            if a.get("seed") and not a.get("createdAt"):
                a["createdAt"] = datetime.now(timezone.utc).isoformat()
            elif not a.get("createdAt"):
                a.pop("seed", None)
        normalized.append(a)
    if corrupt_count:
        log.warning("Normalized %d corrupt entries without filename", corrupt_count)
    return normalized

def git_commit_push(message):
    """Commit and push changes."""
    os.chdir(REPO_DIR)
    
    # Configure git if needed
    run_with_retry(['git', 'config', 'user.email', 'deploy@avatar-gallery'],
                   capture_output=True)
    run_with_retry(['git', 'config', 'user.name', 'Avatar Gallery Deploy Bot'],
                   capture_output=True)
    
    # Add all changes
    result = run_with_retry(['git', 'add', '-A'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  git add failed: {result.stderr}")
        return False
    
    # Check if there are changes to commit
    result = run_with_retry(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if not result.stdout.strip():
        print("  No changes to commit.")
        return True  # Not an error, just nothing to do
    
    # Commit
    result = run_with_retry(['git', 'commit', '-m', message], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  git commit failed: {result.stderr}")
        return False
    print(f"  Committed: {message}")

    # Pull latest before push to avoid rejections (silently handles up-to-date)
    print("  Pulling latest origin/master...")
    run_with_retry(['git', 'pull', '--rebase', 'origin', 'master'], capture_output=True, text=True, timeout=60)

    # Push
    print("  Pushing to origin/master...")
    result = run_with_retry(['git', 'push', 'origin', 'master'], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"  git push failed: {result.stderr}")
        return False
    print(f"  Pushed to origin/master")
    return True

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info("Starting image deploy...")

    lock_fd = None
    try:
        lock_fd = open(LOCK_PATH, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log.warning("Another deploy instance is already running; exiting early.")
        sys.exit(0)
    except OSError as e:
        if lock_fd:
            lock_fd.close()
        raise SystemExit(f"Lock unavailable: {e}")
    
    # Get current state
    repo_images = get_repo_images()
    media_images = get_media_images()
    data = load_data()
    avatars = data.get('avatars', [])
    
    # Canonical image set currently on disk
    repo_image_set = repo_images
    
    # Register images that exist in repo but are missing from data
    existing_by_filename = {a.get('filename', ''): a for a in avatars}
    registered = 0
    dropped = 0
    for filename in sorted(repo_image_set):
        if filename in existing_by_filename:
            continue
        theme = detect_theme(filename)
        prompt = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
        prompt = re.sub(r'\s*\d{8}\s*$', '', prompt)
        prompt = re.sub(r'\s*\d{8}_\d+\s*$', '', prompt)
        prompt = prompt.strip()
        prompt = re.sub(r'^(A|An)\s+', '', prompt, count=1)
        avatar_id = generate_id(filename, theme)
        avatars.append({'id': avatar_id, 'filename': filename, 'prompt': prompt, 'theme': theme})
        registered += 1
        print(f"  Registered missing: {filename}")
    
    # Remove data entries whose files are no longer present on disk
    # Preserve metadata-only entries (seed-based, no filename)
    before_drop = len(avatars)
    avatars = [a for a in avatars if not a.get('filename') or a['filename'] in repo_image_set]
    dropped = before_drop - len(avatars)
    if dropped:
        print(f"  Dropped {dropped} entries missing files")
    
    # Sort newest-first by filename and normalize meta
    avatars.sort(key=lambda a: a.get('filename', ''), reverse=True)
    changed = (len(avatars) != len(data.get('avatars', [])))
    data['avatars'] = avatars
    if changed or registered or dropped:
        now = datetime.now(timezone.utc)
        data['_meta'] = {
            'updatedAt': now.isoformat(),
            'updatedAtTimestamp': int(now.timestamp()),
            'totalImages': len(avatars),
            'lastDeployed': now.strftime('%b %d, %Y at %I:%M %p'),
        }
        save_data(data)
    print(f"  Reconciled data.json (+{registered} registered, -{dropped} dropped, total: {len(avatars)})")
    
    # Find still-new images from media/idle that were just reconciled above
    new_images = {}
    for filename, filepath in media_images.items():
        if filename not in repo_image_set and filename not in existing_by_filename:
            new_images[filename] = filepath
    
    if not new_images:
        print("  No new image files to copy.")
        # Commit any data-only reconciliation or metadata updates
        os.chdir(REPO_DIR)
        result = run_with_retry(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if result.stdout.strip():
            print("  Detected uncommitted data changes — committing.")
            git_commit_push("Sync metadata updates")
        else:
            print("  No changes to deploy.")
        return
    
    print(f"  Found {len(new_images)} new images to deploy.")
    
    # Copy images and build data entries
    new_entries = []
    for filename, filepath in sorted(new_images.items()):
        # Copy to repo
        dest = os.path.join(IMAGES_DIR, filename)
        shutil.copy2(filepath, dest)
        print(f"  Copied: {filename}")
        
        # Detect theme
        theme = detect_theme(filename)
        
        # Generate prompt from filename (human-readable)
        prompt = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
        # Remove date suffixes like _20260619
        prompt = re.sub(r'\s*\d{8}\s*$', '', prompt)
        prompt = re.sub(r'\s*\d{8}_\d+\s*$', '', prompt)
        prompt = prompt.strip()
        # Remove leading "A " or "An "
        prompt = re.sub(r'^(A|An)\s+', '', prompt, count=1)
        
        # Generate ID
        avatar_id = generate_id(filename, theme)
        
        entry = {
            "id": avatar_id,
            "filename": filename,
            "prompt": prompt,
            "theme": theme
        }
        new_entries.append(entry)
        print(f"    → theme: {theme}, prompt: {prompt[:60]}")
    
    # Update data.json
    data['avatars'].extend(new_entries)
    save_data(data)
    print(f"  Updated data.json (+{len(new_entries)} entries, total: {len(data['avatars'])})")
    
    # Git commit and push
    themes_added = set(e['theme'] for e in new_entries)
    commit_msg = f"Deploy {len(new_images)} new images ({', '.join(sorted(themes_added))})"
    success = git_commit_push(commit_msg)
    
    if success:
        print(f"  ✅ Deploy complete! {len(new_entries)} images added.")
        print(f"  GitHub Pages will auto-deploy shortly.")
    else:
        print(f"  ❌ Deploy failed at git step.")

if __name__ == "__main__":
    main()
