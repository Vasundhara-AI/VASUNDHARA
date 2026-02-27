import urllib.request
import os

def download_file(url, outfile):
    print(f"Downloading {url} to {outfile}...")
    if os.path.exists(outfile):
        print("File already exists. Skipping.")
        return
    
    try:
        urllib.request.urlretrieve(url, outfile, reporthook=lambda count, block_size, total_size: print(f"Progress: {count * block_size / total_size * 100:.2f}%", end='\r'))
        print("\nDownload complete.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    if not os.path.exists("models"):
        os.makedirs("models")
    
    # Whisper model
    download_file("https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin", "models/ggml-base.en.bin")
    
    # Phi-3 model
    download_file("https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf", "models/phi-3-mini-4k-instruct.gguf")
