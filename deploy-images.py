#!/usr/bin/env python3
"""
Auto-deploy script for avatar gallery.
Scans /data/hermes/media/images/ for new images, copies them to repo,
updates data.json with theme detection, commits and pushes to GitHub.
"""

import os
import json
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime

SOURCE_DIR = Path("/data/hermes/media/images")
REPO_DIR = Path("/root/avatar-gallery")
IMAGES_DIR = REPO_DIR / "images"
DATA_JSON = REPO_DIR / "data.json"

# Theme detection keywords (order matters - more specific first)
THEME_KEYWORDS = [
    (["lotus"], "lotus"),
    (["dragon", "elf", "wizard", "phoenix", "portal", "rune", "enchant", "magic"], "fantasy"),
    (["cyber", "robot", "space", "astronaut", "neon", "chrome", "alien", "ship"], "sci-fi"),
    (["mountain", "lake", "forest", "ocean", "flower", "tree", "wolf", "butterfly", "sunset"], "nature"),
    (["abstract", "fractal", "geometric", "fluid", "marble", "gradient", "glitch", "spiral", "mandala"], "abstract"),
    (["divine", "providence", "yggdrasil", "ankh", "egyptian", "norse", "god", "sacred", "cosmic"], "mythology"),
    (["tattoo", "ink", "brush", "sumi", "woodblock", "ukiyo"], "tattoo"),
    (["watercolor", "wash", "paint"], "watercolor"),
    (["minimal", "line", "simple", "clean", "continuous"], "minimalist"),
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
    # Remove extension and date patterns
    prompt = filename
    for pattern in CLEAN_PATTERNS:
        prompt = re.sub(pattern, " ", prompt, flags=re.IGNORECASE)
    
    # Replace underscores with spaces
    prompt = prompt.replace("_", " ")
    
    # Clean up multiple spaces
    prompt = re.sub(r"\s+", " ", prompt).strip()
    
    # Title case
    prompt = prompt.title()
    
    # Fix common acronyms
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
    }.get(theme, "uncategorized")
    
    # Find highest existing number for this theme
    max_num = 0
    for avatar in existing_avatars:
        if avatar["id"].startswith(theme_prefix + "_"):
            try:
                num = int(avatar["id"].split("_")[-1])
                max_num = max(max_num, num)
            except (ValueError, IndexError):
                pass
    
    return f"{theme_prefix}_{max_num + 1:02d}"


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
    
    # Ensure images directory exists
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get existing files
    existing_filenames = get_existing_filenames(DATA_JSON)
    existing_image_files = get_existing_image_files(IMAGES_DIR)
    print(f"Existing in data.json: {len(existing_filenames)}")
    print(f"Existing in images/: {len(existing_image_files)}")
    
    # Load current data.json
    if DATA_JSON.exists():
        with open(DATA_JSON) as f:
            data = json.load(f)
    else:
        data = {"avatars": [], "metadata": {}}
    
    avatars = data.get("avatars", [])
    
    # Scan source directory for new images
    new_images = []
    for img_path in SOURCE_DIR.iterdir():
        if not img_path.is_file():
            continue
        if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue
        if img_path.name in existing_filenames or img_path.name in existing_image_files:
            continue
        new_images.append(img_path)
    
    print(f"Found {len(new_images)} new images to deploy")
    
    if not new_images:
        print("No new images to deploy. Exiting.")
        return 0
    
    # Process each new image
    added_count = 0
    for img_path in new_images:
        filename = img_path.name
        
        # Detect theme and generate prompt
        theme = detect_theme(filename)
        prompt = generate_prompt(filename)
        avatar_id = get_next_id(theme, avatars)
        
        # Copy image to repo
        dest_path = IMAGES_DIR / filename
        shutil.copy2(img_path, dest_path)
        print(f"Copied: {filename} -> {dest_path}")
        
        # Add to avatars list
        new_avatar = {
            "id": avatar_id,
            "filename": filename,
            "prompt": prompt,
            "theme": theme
        }
        avatars.append(new_avatar)
        added_count += 1
        print(f"  Added: {avatar_id} | Theme: {theme} | Prompt: {prompt}")
    
    if added_count == 0:
        print("No new images added.")
        return 0
    
    # Update metadata
    themes = sorted(set(a["theme"] for a in avatars))
    data["avatars"] = avatars
    data["metadata"] = {
        "total": len(avatars),
        "themes": themes,
        "images_per_theme": len(avatars) // len(themes) if themes else 0,
        "format": "512x512 JPEG",
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "attribution": "Images generated via Pollinations.ai (Flux model) — free AI image generation API. https://pollinations.ai"
    }
    
    # Write updated data.json
    with open(DATA_JSON, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Updated data.json: {len(avatars)} total avatars")
    
    # Git operations
    print("\nCommitting and pushing to GitHub...")
    
    # Add all changes
    if not run_git_command("git add images/ data.json"):
        return 1
    
    # Commit
    commit_msg = f"Auto-deploy: Add {added_count} new images ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
    if not run_git_command(f'git commit -m "{commit_msg}"'):
        print("No changes to commit or commit failed")
        return 1
    
    # Push
    if not run_git_command("git push origin master"):
        print("Push failed")
        return 1
    
    print("Push successful! GitHub Pages will deploy automatically.")
    print(f"\nCompleted: {datetime.now().isoformat()}")
    print(f"Added {added_count} images")
    return 0


if __name__ == "__main__":
    exit(main())