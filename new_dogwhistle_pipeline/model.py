import json
import logging
import torch
from transformers import AutoModelForMultimodalLM, AutoProcessor

logger = logging.getLogger(__name__)

#System instructions defining the dog whistle detection task and expected output behavior
system_prompt = """You are a helpful assistant participating in a content moderation task of
    dog whistle detection. A dog whistle is the use of coded or suggestive
    language in political messaging to garner support from a particular group
    without provoking opposition. The concept is named after ultrasonic dog
    whistles, which are audible to dogs but not humans. Dog whistles use
    language that appears normal to the majority but communicates specific
    things to intended audiences. They are generally used to convey messages
    on issues likely to provoke controversy without attracting negative attention."""



class DogWhistleDetector:
"""Run batch inference to detect dog whistles."""

    def __init__(self, model_id: str, max_new_tokens: int = 256):
        self.max_new_tokens = max_new_tokens
        self.processor = AutoProcessor.from_pretrained(model_id)

        tokenizer = getattr(self.processor, "tokenizer", self.processor)
        tokenizer.padding_side = "left"
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForMultimodalLM.from_pretrained(model_id, dtype=dtype, device_map="auto",)
        self.model.eval()

    def _build_messages(self, formatted_post: str) -> list[dict]:
        """Build chat messages asking the model to return a strict JSON result."""
        user_prompt = (
            "Does the following post contain dog whistles? If it does, identify the "
            "dog whistles.\n"
            f'"""\n{formatted_post}\n"""\n'
            'Respond ONLY with valid JSON in the exact format: {"dogwhistles": ["..."]}. '
            "Use an empty list if none are found."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _run_inference(self, texts: list[str]) -> list[str]:
        """Tokenize a batch of formatted posts, generate completions, and decode new tokens."""
        batch_messages = [self._build_messages(t) for t in texts]

        inputs = self.processor.apply_chat_template(
            batch_messages,
            add_generation_prompt=True,
            tokenize=True,
            padding=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)

        input_len = inputs["input_ids"].shape[-1]
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
            )

        generated = outputs[:, input_len:]
        return [
            self.processor.decode(seq, skip_special_tokens=True).strip()
            for seq in generated
        ]

    def predict_batch(self, texts: list[str]) -> list[dict]:
        try:
            raw_outputs = self._run_inference(texts)
        except torch.cuda.OutOfMemoryError:
            logger.warning("Out of memory text to long", len(texts))
            torch.cuda.empty_cache()
            raw_outputs = []
            for text in texts:
                try:
                    raw_outputs.extend(self._run_inference([text]))
                except torch.cuda.OutOfMemoryError:
                    torch.cuda.empty_cache()
                    raw_outputs.append("")

        return [self._parse_output(raw) for raw in raw_outputs]

    @staticmethod
    def _parse_output(raw_output: str) -> dict:
        """Parse the model response into a structured dictionary."""
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and isinstance(parsed.get("dogwhistles"), list):
                return {
                    "dogwhistles": parsed["dogwhistles"],
                    "parsed": True,
                    "raw_output": raw_output,
                }
        except json.JSONDecodeError:
            pass

        return {
            "dogwhistles": [],
            "parsed": False,
            "raw_output": raw_output,
        }