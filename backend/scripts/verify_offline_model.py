import os
# Force offline
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

try:
    from sentence_transformers import SentenceTransformer
    print("Verification: Attempting to load model OFFLINE...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', local_files_only=True)
    print(f"Verification: SUCCESS! Model loaded from local cache.")
    
    # Test a small embedding
    vec = model.encode("Hello world")
    print(f"Verification: Embedding generated (dim: {len(vec)})")
except Exception as e:
    print(f"Verification: FAILED - {e}")
    print("If this failed, it means the model is not in the default Hugging Face cache directory.")
