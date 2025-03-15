import json
import requests
from tqdm import tqdm

# Hugging Face API settings
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HEADERS = {"Authorization": f"Bearer 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"}

def query_huggingface_api(text):
    """
    Sends a summarization request to Hugging Face API.
    """
    payload = {"inputs": text, "parameters": {"max_length": 130, "min_length": 50, "do_sample": False}}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        return response.json()[0]["summary_text"]
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def extractive_summary(chunks, topics, gambits, top_n=5):
    """
    Extract key sentences based on relevance to topics, gambits, and connectivity.
    """
    text = " ".join(chunks)
    sentences = text.split(". ")
    sentences = [s.strip() for s in sentences if len(s) > 10]  # Remove very short sentences

    # Basic keyword matching for relevance scoring
    relevance_scores = [
        sum(1 for keyword in (topics + gambits) if keyword.lower() in sentence.lower())
        for sentence in sentences
    ]

    # Add connectivity scoring (simple heuristic: longer sentences might offer more context)
    connectivity_scores = [len(sentence.split()) for sentence in sentences]

    # Combine relevance and connectivity scores
    combined_scores = [
        relevance + 0.5 * connectivity
        for relevance, connectivity in zip(relevance_scores, connectivity_scores)
    ]

    # Rank sentences by combined score
    ranked_sentences = sorted(
        zip(combined_scores, sentences), key=lambda x: x[0], reverse=True
    )

    # Select top N relevant and diverse sentences
    selected_sentences = []
    for _, sentence in ranked_sentences:
        if len(selected_sentences) >= top_n:
            break
        if sentence not in selected_sentences:
            selected_sentences.append(sentence)

    return selected_sentences

def summarize_articles(input_file="processed_articles.json", output_file="summarized_articles.json"):
    """
    Summarize articles using extractive and Hugging Face abstractive methods.
    """
    with open(input_file, "r", encoding="utf-8") as f:
        articles = json.load(f)

    summarized_articles = []

    for article in tqdm(articles, desc="Summarizing articles"):
        title = article.get("Title", "No Title")
        url = article.get("url", "")
        chunks = article.get("chunks", [])
        entities = article.get("entities", {})

        # Extract topics and gambits
        topics = entities.get("Topics", [])
        gambits = entities.get("Gambits", [])

        # Step 1: Extractive summarization
        extractive_sentences = extractive_summary(chunks, topics, gambits)

        # Step 2: Abstractive summarization using Hugging Face API
        abstractive_text = query_huggingface_api(" ".join(extractive_sentences))

        summarized_articles.append({
            "Title": title,
            "url": url,
            "extractive_summary": " ".join(extractive_sentences),
            "abstractive_summary": abstractive_text or "API request failed",
            "entities": entities
        })

    # Save summarized articles to output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summarized_articles, f, ensure_ascii=False, indent=2)

    print(f"Summarized {len(summarized_articles)} articles. Saved to {output_file}.")

if __name__ == "__main__":
    summarize_articles()
