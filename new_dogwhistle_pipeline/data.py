import json
from itertools import islice
from pathlib import Path
from typing import Iterator


def load_processed_ids(output_path: Path) -> set[str]:
    """Load post_id values already present in an output JSONL file."""
    #Return an empty set if no output file exists yet
    if not output_path.exists():
        return set()

    processed = set()
    with open(output_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if "post_id" in record:
                    processed.add(str(record["post_id"]))
            #Skip incomplete or corrupted lines        
            except json.JSONDecodeError:
                continue
    return processed


def iter_pending_posts(input_path: Path, processed_ids: set[str], max_comments: int, max_chars: int,) -> Iterator[dict]:
    """Yield formatted records for posts in input_path not yet in processed_ids."""
    with open(input_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    items = (raw_data.items() if isinstance(raw_data, dict) else enumerate(raw_data))

    for key, post in items:
        post_id = str(post.get("id", key))
        if post_id in processed_ids:
            continue

        yield {
            "post_id": post_id,
            "source_file": input_path.name,
            "title": post.get("title", ""),
            "formatted_text": format_post(post, max_comments, max_chars),
        }


def format_post(post: dict, max_comments: int, max_chars: int) -> str:
    """Format a post and up to max_comments comments into a truncated text block."""
    title = post.get("title", "")
    selftext = post.get("selftext", "")
    comments = post.get("comments", [])[:max_comments]

    formatted_comments = "\n".join(
        f"\ttext: {c.get('body', '')}" for c in comments if c.get("body")
    )

    full_text = (
        f"title: {title},\n"
        f"post_text: {selftext},\n"
        f"comments: [\n{formatted_comments}\n]"
    )
    return full_text[:max_chars]


def batch_iterator(iterable: Iterator[dict], batch_size: int) -> Iterator[list[dict]]:
    """Group items from an iterator into lists of at most batch_size elements."""
    while batch := list(islice(iterable, batch_size)):
        yield batch