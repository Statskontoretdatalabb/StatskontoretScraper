from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import HfApi

DEFAULT_DATASET_REPO_ID = "Statskontoretdatalabb/StatskontoretWebsites"


def publish_artifacts(
    artifact_dir: Path,
    dataset_repo_id: str = DEFAULT_DATASET_REPO_ID,
) -> None:
    load_dotenv()
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN is not set. Add it to the environment or .env.")

    if not artifact_dir.exists():
        raise RuntimeError(f"Artifact directory does not exist: {artifact_dir}")

    api = HfApi(token=token)
    api.upload_folder(
        repo_id=dataset_repo_id,
        folder_path=str(artifact_dir),
        path_in_repo=".",
        repo_type="dataset",
        commit_message="Update generated website dataset",
    )
