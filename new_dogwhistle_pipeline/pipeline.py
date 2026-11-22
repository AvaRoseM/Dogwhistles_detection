import json
import logging
from pathlib import Path
from tqdm import tqdm

from config import PipelineConfig
from data import batch_iterator, iter_pending_posts, load_processed_ids
from model import DogWhistleDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def process_single_file(detector: DogWhistleDetector, input_file: Path, output_file: Path, cfg: PipelineConfig,) -> int:
    """Run batch inference on a single JSON file and append results to a JSONL file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    processed_ids = load_processed_ids(output_file)
    logger.info(
        "[%s] %d posts already processed -> output : %s",
        input_file.name,
        len(processed_ids),
        output_file,
    )

    pending_posts = iter_pending_posts(
        input_path=input_file,
        processed_ids=processed_ids,
        max_comments=cfg.max_comments_per_post,
        max_chars=cfg.max_chars_per_post,
    )

    written_for_file = 0
    with open(output_file, mode="a", encoding="utf-8") as out_file:
        for batch in tqdm(
            batch_iterator(pending_posts, cfg.batch_size),
            desc=input_file.name,
        ):
            texts = [item["formatted_text"] for item in batch]
            predictions = detector.predict_batch(texts)

            for item, pred in zip(batch, predictions):
                record = {
                    "post_id": item["post_id"],
                    "source_file": item["source_file"],
                    "title": item["title"],
                    **pred,
                }
                out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                written_for_file += 1

            out_file.flush()

    logger.info(
        "[%s] Finish : %d saved new posts.",
        input_file.name,
        written_for_file,
    )
    return written_for_file


def run_pipeline(cfg: PipelineConfig) -> None:
    """Resolve input files, load the detector once, and process all matching inputs."""
    input_files = cfg.resolve_input_files()
    if not input_files:
        logger.warning("No json file found for : %s", cfg.input_paths)
        return

    logger.info("%d json files to process : %s", len(input_files), [str(p) for p in input_files])

    # Load model weights once and reuse across all input files
    detector = DogWhistleDetector(
        model_id=cfg.model_id,
        max_new_tokens=cfg.max_new_tokens,
    )

    grand_total = 0
    for input_file in input_files:
        output_file = cfg.output_path_for(input_file)
        grand_total += process_single_file(detector, input_file, output_file, cfg)

    logger.info("Pipeline over : %d new posts.", grand_total)


if __name__ == "__main__":
    run_pipeline(PipelineConfig(input_paths=(Path("json_files"),)))