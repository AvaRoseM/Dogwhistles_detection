import os
from dataclasses import dataclass, field
from pathlib import Path

#Load HF and Torch cache in the node temporary storage
os.environ.setdefault("HF_HOME", "/tmp/huggingface_cache")
os.environ.setdefault("TORCH_HOME", "/tmp/torch-cache")


@dataclass(frozen=True)
class PipelineConfig:
    """Default immutable configuration for the inference pipeline.

    Attributes:
    model_id: Model identifier on Hugging Face.
    input_paths: File paths, glob patterns, or directories containing input JSON files.
    output_dir: Destination directory for output files (defaults to ~/outputs).
    output_prefix: Prefix added to each output filename.
    batch_size: Batch size used during inference.
    max_new_tokens: Maximum number of tokens generated per output.
    max_comments_per_post: Maximum number of comments kept per post.
    max_chars_per_post: Maximum number of characters allowed per post.
    """
    model_id: str = "Qwen/Qwen3.5-9B" 
    input_paths: tuple[Path, ...] = field(
        default_factory=lambda: (
            #Default file
            Path("json_files/4chan_09_11.json"),
        )
    )

    output_dir: Path = field(default_factory=lambda: Path.home() / "outputs")
    output_prefix: str = "dogwhistles_"
    batch_size: int = 4
    max_new_tokens: int = 256
    max_comments_per_post: int = 9999
    max_chars_per_post: int = 999999


    def resolve_input_files(self) -> list[Path]:
        """Resolve 'input_paths' into a deduplicated list of existing .json files.

        Supports glob patterns ('*', '?', '['), directories, and individual file paths.
        Raises FileNotFoundError if a target path does not exist.
        """
        resolved: list[Path] = []
        seen: set[Path] = set()

        for raw_path in self.input_paths:
            path_str = str(raw_path)
            if any(ch in path_str for ch in ("*", "?", "[")):
                matches = sorted(Path().glob(path_str))
            else:
                matches = [raw_path]

            for p in matches:
                # If p is a directory, collect all .json files inside it
                candidates = sorted(p.glob("*.json")) if p.is_dir() else [p]
                for file_path in candidates:
                    if not file_path.exists():
                        raise FileNotFoundError(f"Fichier introuvable : {file_path}")
                    if file_path.suffix.lower() != ".json":
                        continue
                    #Use the resolved path to avoid duplicates
                    abs_path = file_path.resolve()
                    if abs_path not in seen:
                        seen.add(abs_path)
                        resolved.append(file_path)

        return resolved

    def output_path_for(self, input_file: Path) -> Path:
        """Generate the output .jsonl path corresponding to an input JSON file."""
        return self.output_dir / f"{self.output_prefix}{input_file.stem}.jsonl"