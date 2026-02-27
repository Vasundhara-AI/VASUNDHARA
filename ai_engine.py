from llama_cpp import Llama

from config import LLM_MAX_TOKENS, LLM_MODEL_PATH

class AIEngine:
    def __init__(self):
        print(f"Loading LLM model: {LLM_MODEL_PATH}...")
        self.llm = Llama(model_path=LLM_MODEL_PATH, n_ctx=2048, verbose=False)

    def generate_response(self, text):
        user_tag = "<|user|>"
        end_tag = "<|end|>"
        assistant_tag = "<|assistant|>"
        prompt = f"{user_tag}\n{text}{end_tag}\n{assistant_tag}"
        output = self.llm(prompt, max_tokens=LLM_MAX_TOKENS, stop=[end_tag], echo=False)
        return output["choices"][0]["text"].strip()
