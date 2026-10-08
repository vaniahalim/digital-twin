"""Publish this repo to the Hugging Face Space (the Space mirrors the repo; edit here, not there)."""
import os
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

SPACE_ID = "vaniacrystal/career_conversation"
FRONT_MATTER = """---
title: career_conversation
app_file: app.py
sdk: gradio
sdk_version: 5.49.1
---

"""
ROOT = Path(__file__).resolve().parent.parent
INCLUDE = ["app.py", "requirements.txt", "me"]

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    for name in INCLUDE:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, out / name)
        else:
            shutil.copy2(src, out / name)
    (out / "README.md").write_text(FRONT_MATTER + (ROOT / "README.md").read_text())
    HfApi(token=os.environ["HF_TOKEN"]).upload_folder(
        folder_path=str(out),
        repo_id=SPACE_ID,
        repo_type="space",
        delete_patterns=["*"],
        commit_message=f"Deploy from GitHub {os.environ.get('GITHUB_SHA', 'local')[:7]}",
    )
print("Deployed to", SPACE_ID)
