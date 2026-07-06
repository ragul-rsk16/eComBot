"""
embed_catalog.py — Load and embed ecommerce products and FAQs with ChromaDB
---------------------------------------------------------------------------
Loads product catalog from data/products.json and FAQs from data/faq.json,
creating embeddings using OpenRouter's OpenAI embedding endpoint via LiteLlm.

Pipeline:
    1. Load products from data/products.json and FAQs from data/faq.json
    2. Embed text (product: name + category; FAQ: question + answer) using EMBEDDING_MODEL
    3. Upsert both into in-memory ChromaDB collection for semantic search
    4. Query embeddings for top_k nearest products/FAQs by vector distance
"""

import os
import json
import chromadb
import litellm
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "openrouter/openai/text-embedding-3-small"
COLLECTION_NAME = "ecombot_kb"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"

def embed(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via OpenRouter's OpenAI-compatible /embeddings endpoint."""
    response = litellm.embedding(
        model=EMBEDDING_MODEL,
        input=texts,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    return [item["embedding"] for item in response.data]


def _load_products() -> list[dict]:
    """Load products from data/products.json and prepare for embedding."""
    with open(PRODUCTS_FILE, "r") as f:
        products = json.load(f)
    return products


def _load_faqs() -> list[dict]:
    """Load FAQs from data/faq.json."""
    faq_file = DATA_DIR / "faq.json"
    with open(faq_file, "r") as f:
        faqs = json.load(f)
    return faqs


def _prepare_product_text(product: dict) -> str:
    """Convert a product dict to embeddable text combining name and category."""
    name = product.get("name", "")
    category = product.get("category", "")
    return f"{name} {category}".strip()


def _prepare_faq_text(faq: dict) -> str:
    """Convert an FAQ dict to embeddable text combining question and answer."""
    question = faq.get("question", "")
    text = faq.get("text", "")
    return f"{question} {text}".strip()


# Opened once per process — building the collection means embedding every
# product, so it's worth caching the client/collection as a singleton.
_collection = None


def _get_collection():
    """Return the (lazily indexed) in-memory ChromaDB collection of PRODUCTS and FAQs."""
    global _collection
    if _collection is None:
        client = chromadb.EphemeralClient()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Load and prepare products
        products = _load_products()
        product_texts = [_prepare_product_text(p) for p in products]
        product_ids = [p["id"] for p in products]
        
        # Load and prepare FAQs
        faqs = _load_faqs()
        faq_texts = [_prepare_faq_text(f) for f in faqs]
        faq_ids = [f["id"] for f in faqs]
        
        # Combine products and FAQs
        all_ids = product_ids + faq_ids
        all_texts = product_texts + faq_texts
        all_embeddings = embed(all_texts)
        
        # Upsert both into collection
        collection.upsert(
            ids=all_ids,
            documents=all_texts,
            embeddings=all_embeddings,
        )
        _collection = collection
    return _collection


def semantic_search(query: str, top_k: int = 3) -> list[dict]:
    """
    Return the top_k products whose embeddings are closest — by vector
    distance, as judged by ChromaDB — to the query's embedding.

    Each result is a dict: {"id", "text", "score"} where score is a
    similarity in [0, 1] derived from ChromaDB's distance (higher = closer
    match), so callers don't need to know which distance metric is in use.
    Returns an empty list for an empty query.
    """
    if not query or not query.strip():
        return []

    collection = _get_collection()
    result = collection.query(
        query_embeddings=embed([query.strip()]),
        n_results=min(top_k, collection.count()),
    )

    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    return [
        {"id": doc_id, "text": text, "score": 1.0 / (1.0 + distance)}
        for doc_id, text, distance in zip(ids, documents, distances)
    ]
