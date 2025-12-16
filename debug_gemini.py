import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("EMBEDDING_API_KEY")
if not api_key:
    print("Error: EMBEDDING_API_KEY not found in environment")
    exit(1)

genai.configure(api_key=api_key)

texts = ["This is a test document.", "Another test document."]
model = "models/embedding-001"

try:
    print(f"Testing embedding with model: {model}")
    print(f"Input texts: {texts}")
    
    result = genai.embed_content(
        model=model,
        content=texts,
        task_type="retrieval_document"
    )
    
    print("\n--- Result Debug Info ---")
    print(f"Result type: {type(result)}")
    print(f"Result keys (if dict): {result.keys() if isinstance(result, dict) else 'N/A'}")
    print(f"Result content: {result}")
    
    if isinstance(result, dict) and 'embedding' in result:
        print(f"\n'embedding' field type: {type(result['embedding'])}")
        print(f"'embedding' field length: {len(result['embedding'])}")
        
except Exception as e:
    print(f"Error: {e}")

