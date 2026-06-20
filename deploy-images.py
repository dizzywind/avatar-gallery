#!/usr/bin/env python3
"""
Auto-deploy script for avatar gallery.
Scans /data/hermes/media/images/ for new images, copies them to repo,
updates data.json with theme detection, commits and pushes to GitHub.
"""

import hashlib
import os
import json
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime, timezone

SOURCE_DIR = Path("/data/hermes/media/images")
REPO_DIR = Path("/data/projects/avatar-gallery")
IMAGES_DIR = REPO_DIR / "images"
DATA_JSON = REPO_DIR / "data.json"
IDLE_STAGING_DIR = REPO_DIR / "data" / "idle"

# Theme detection keywords (order matters - more specific first)
THEME_KEYWORDS = [
    (["lotus"], "lotus"),
    (["dragon", "elf", "wizard", "phoenix", "portal", "rune", "enchant", "magic"], "fantasy"),
    (["cyber", "robot", "space", "astronaut", "neon", "chrome", "alien", "ship"], "sci-fi"),
    (["mountain", "lake", "forest", "ocean", "flower", "tree", "wolf", "butterfly", "sunset", "coral", "reef", "underwater", "wildflower", "nature"], "nature"),
    (["abstract", "fractal", "geometric", "fluid", "marble", "gradient", "glitch", "spiral", "mandala", "calligraphy", "brush", "expressionist", "chaotic"], "abstract"),
    (["divine", "providence", "yggdrasil", "ankh", "egyptian", "norse", "god", "sacred", "cosmic", "celestial", "eye"], "mythology"),
    (["tattoo", "ink", "brush", "sumi", "woodblock", "ukiyo", "tribal"], "tattoo"),
    (["watercolor", "wash", "paint", "devotional"], "watercolor"),
    (["minimal", "line", "simple", "clean", "continuous", "single", "zen"], "minimalist"),
    (["portrait", "avatar", "character", "face", "handsome", "elfen", "mage", "warrior", "elegant", "playful", "pastel", "artdeco", "dark", "concept", "assistant", "ai", "anime", "named", "hermes"], "portrait"),
    (["dog", "cat", "animal", "guardian", "ghibli", "wolf", "creature"], "animals"),
    (["retro", "synthwave", "1970s", "1980s", "disco", "80s", "70s"], "retro"),
]

# Patterns to strip from filename for prompt generation
CLEAN_PATTERNS = [
    r"^A_",
    r"^Abstract_",
    r"_2026\d{4}$",
    r"_\d{4}$",
    r"\.jpg$",
    r"\.jpeg$",
    r"\.png$",
    r"_+",
]


def get_existing_filenames(data_json_path):
    """Get set of existing filenames from data.json"""
    if not data_json_path.exists():
        return set()
    with open(data_json_path) as f:
        data = json.load(f)
    return {avatar["filename"] for avatar in data.get("avatars", [])}


def get_existing_image_files(images_dir):
    """Get set of existing image files in repo"""
    if not images_dir.exists():
        return set()
    return {f.name for f in images_dir.iterdir() if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png"]}


def get_existing_image_hashes(images_dir):
    """Return {filename: md5_hex} for current repo images."""
    hashes = {}
    for f in sorted(images_dir.iterdir()):
        if not f.is_file() or f.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue
        with open(f, "rb") as fp:
            hashes[f.name] = hashlib.md5(fp.read()).hexdigest()
    return hashes


def detect_theme(filename):
    """Detect theme from filename using keyword matching"""
    filename_lower = filename.lower()
    for keywords, theme in THEME_KEYWORDS:
        for keyword in keywords:
            if keyword in filename_lower:
                return theme
    return "uncategorized"


def generate_prompt(filename):
    """Generate human-readable prompt from filename"""
    prompt = filename
    for pattern in CLEAN_PATTERNS:
        prompt = re.sub(pattern, " ", prompt, flags=re.IGNORECASE)

    prompt = prompt.replace("_", " ")
    prompt = re.sub(r"\s+", " ", prompt).strip()
    prompt = prompt.title()
    prompt = prompt.replace("Ai ", "AI ").replace("A I", "AI")
    return prompt


def get_next_id(theme, existing_avatars):
    """Generate next ID for a theme"""
    theme_prefix = {
        "fantasy": "fantasy",
        "sci-fi": "scifi",
        "nature": "nature",
        "abstract": "abstract",
        "mythology": "mythology",
        "lotus": "lotus",
        "tattoo": "tattoo",
        "watercolor": "watercolor",
        "minimalist": "minimalist",
        "uncategorized": "uncategorized",
        "portrait": "portrait",
        "animals": "animals",
        "retro": "retro",
    }.get(theme, "uncategorized")

    max_num = 0
    for avatar in existing_avatars:
        if avatar["id"].startswith(theme_prefix + "_"):
            try:
                num = int(avatar["id"].split("_")[-1])
                max_num = max(max_num, num)
            except (ValueError, IndexError):
                pass

    return f"{theme_prefix}_{max_num + 1:02d}"


def sort_avatars(avatars):
    """Sort avatars newest-first based on date in filename; ties/without-date go last."""

    def sort_key(a):
        m = re.search(r'(20\d{6})', a.get('filename', ''))
        return (m.group(1) if m else '00000000', a.get('filename', ''))

    return sorted(avatars, key=sort_key, reverse=True)


def run_git_command(cmd, cwd=REPO_DIR):
    """Run a git command and return result"""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"Git command failed: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False
    return True


def main():
    print("=" * 60)
    print("Avatar Gallery Auto-Deploy")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    IDLE_STAGING_DIR.mkdir(parents=True, exist_ok=True)

    existing_filenames = get_existing_filenames(DATA_JSON)
    existing_image_files = get_existing_image_files(IMAGES_DIR)
    existing_image_hashes = get_existing_image_hashes(IMAGES_DIR)
    print(f"Existing in data.json: {len(existing_filenames)}")
    print(f"Existing in images/: {len(existing_image_files)}")

    copied_from_idle = 0
    for idle_path in sorted(IDLE_STAGING_DIR.iterdir()):
        if not idle_path.is_file():
            continue
        if idle_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue
        if idle_path.name in existing_filenames or idle_path.name in existing_image_files:
            continue
        if idle_path.exists() and idle_path.stat().st_size == 0:
            continue
        try:
            shutil.copy2(idle_path, SOURCE_DIR / idle_path.name)
            copied_from_idle += 1
            print(f"Copied from idle output: {idle_path.name}")
        except Exception as e:
            print(f"Idle copy failed for {idle_path.name}: {e}")
    if copied_from_idle:
        print(f"Copied {copied_from_idle} images from idle output to media store")

    if DATA_JSON.exists():
        with open(DATA_JSON) as f:
            data = json.load(f)
    else:
        data = {"avatars": [], "metadata": {}}

    avatars = data.get("avatars", [])
    existing_avatars = list(avatars)
    avatars = sort_avatars(avatars)

    backfilled = 0
    for avatar in avatars:
        theme = avatar.get("theme")
        if avatar.get("category") is None and theme:
            avatar["category"] = theme
            backfilled += 1
    if backfilled:
        print(f"Backfilled category for {backfilled} existing avatars")

    new_images = []
    empty_skips = []
    dup_skips = []
    for img_path in SOURCE_DIR.iterdir():
        if not img_path.is_file():
            continue
        if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue
        if img_path.name in existing_filenames or img_path.name in existing_image_files:
            dup_skips.append(img_path.name)
            continue
        if img_path.exists() and img_path.stat().st_size == 0:
            empty_skips.append(img_path.name)
            continue
        new_images.append(img_path)

    print(f"Found {len(new_images)} new images to deploy")
    if empty_skips:
        print(f"Skipped {len(empty_skips)} 0-byte source images")
    if dup_skips:
        print(f"Skipped {len(dup_skips)} source files already in repo")
    if not new_images:
        print("No new images to deploy. Exiting.")
        return 0

    added_count = 0
    for img_path in new_images:
        filename = img_path.name

        if not img_path.exists() or img_path.stat().st_size == 0:
            print(f"Skipping 0-byte source image: {filename}")
            empty_skips.append(filename)
            continue

        source = img_path.read_bytes()
        source_hash = hashlib.md5(source).hexdigest()
        if source_hash in existing_image_hashes.values():
            print(f"Skipping duplicate content for: {filename}")
            dup_skips.append(filename)
            continue

        theme = detect_theme(filename)
        prompt = generate_prompt(filename)
        avatar_id = get_next_id(theme, existing_avatars)
        dest_path = IMAGES_DIR / filename

        shutil.copy2(img_path, dest_path)
        existing_image_hashes[filename] = source_hash
        print(f"Copied: {filename} -> {dest_path}")

        new_avatar = {
            "id": avatar_id,
            "filename": filename,
            "prompt": prompt,
            "theme": theme,
            "category": theme,
        }
        avatars.append(new_avatar)
        existing_avatars.append(new_avatar)
        added_count += 1
        print(f"  Added: {avatar_id} | Theme: {theme} | Prompt: {prompt}")

    if added_count == 0:
        print("No new images added.")
        return 0

    themes = sorted({a["theme"] for a in avatars})
    data["avatars"] = avatars
    data["metadata"] = {
        "total": len(avatars),
        "themes": themes,
        "images_per_theme": len(avatars) // len(themes) if themes else 0,
        "format": "512x512 JPEG",
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "attribution": "Images generated via Pollinations.ai (Flux model) — free AI image generation API. https://pollinations.ai"
    }
    data["_meta"] = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "updatedAtTimestamp": int(datetime.now(timezone.utc).timestamp()),
        "totalImages": len(avatars),
        "lastDeployed": datetime.now(timezone.utc).strftime("%b %d, %Y at %I:%M %p"),
    }

    with open(DATA_JSON, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Updated data.json: {len(avatars)} total avatars")

    print("\nCommitting and pushing to GitHub...")

    if not run_git_command("git add -A"):
        return 1

    commit_msg = f"Auto-deploy: Add {added_count} new images ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
    if not run_git_command(f'git commit -m "{commit_msg}"'):
        print("No changes to commit or commit failed")
        return 1

    if not run_git_command("git fetch origin master"):
        print("Fetch failed")
        return 1
    if not run_git_command("git rebase origin/master"):
        print("Rebase failed")
        return 1

    if not run_git_command("git push origin master"):
        print("Push failed")
        return 1

    print("Push successful! GitHub Pages will deploy automatically.")
    print(f"\nCompleted: {datetime.now().isoformat()}")
    print(f"Added {added_count} images")
    return 0


if __name__ == "__main__":
    exit(main())
