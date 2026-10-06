import hashlib
from pathlib import Path


class PromptRegistry:
    """Manages prompt templates and computes content hashes for run tracking."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(__file__).parent

    def load(self, category: str, version: str) -> str:
        """
        Loads prompt template file, e.g. load("extraction", "v2").
        """
        category_dir = self.base_dir / category
        for file in category_dir.glob(f"{version}_*.txt"):
            return file.read_text(encoding="utf-8")

        # Fallback to any matching version prefix
        for file in category_dir.glob("*.txt"):
            if version in file.name:
                return file.read_text(encoding="utf-8")

        raise FileNotFoundError(
            f"Prompt template for category '{category}' version '{version}' not found in {category_dir}"
        )

    def hash(self, template: str) -> str:
        """Computes a 16-character SHA-256 hash of the prompt template string."""
        return hashlib.sha256(template.encode("utf-8")).hexdigest()[:16]
