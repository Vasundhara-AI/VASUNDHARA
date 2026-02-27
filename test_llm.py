from llama_cpp import Llama
import os

model_path = "models/phi-3-mini-4k-instruct.gguf"
if not os.path.exists(model_path):
    print(f"Model not found at {model_path}")
else:
    print(f"Loading model: {model_path}...")
    try:
        llm = Llama(model_path=model_path, n_ctx=512, verbose=True)
        print("Model loaded successfully!")
        output = llm("Q: What is 2+2? A:", max_tokens=10)
        print(f"Test output: {output['choices'][0]['text']}")
    except Exception as e:
        print(f"Error loading model: {e}")
