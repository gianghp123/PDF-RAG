import os
import dotenv

dotenv.load_dotenv()

llm_config = {
    "model_name": "models/gemini-2.0-flash-lite-preview-02-05",
    "api_key": os.environ.get("LLM_API_KEY"),
    "base_url": os.environ.get("LLM_BASE_URL"),
}

embedding_config = {
    "model_name": "jinaai/jina-embeddings-v2-small-en",  # FastEmbedEmbeddings
    "max_length": 1000,
    "batch_size": 64,
}

reranker_config = {
    "model_name": "jinaai/jina-reranker-v1-tiny-en"
}  # FastEmbed TextCrossEncoder