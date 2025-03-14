import json
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Download NLTK data if not already done
nltk.download("punkt")

def extractive_summary(text, num_sentences=3):
    """
    Generates a high-level extractive summary by selecting the most important sentences.
    """
    sentences = sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return text

    # Use TF-IDF to score sentence importance
    vectorizer = TfidfVectorizer(stop_words="english")
    sentence_vectors = vectorizer.fit_transform(sentences)
    # Score each sentence by summing its TF-IDF values
    scores = np.array(sentence_vectors.sum(axis=1)).flatten()

    # Get indices of top sentences and sort them in original order
    top_indices = scores.argsort()[-num_sentences:][::-1]
    selected_indices = sorted(top_indices)
    summary = " ".join([sentences[i] for i in selected_indices])
    return summary

def summarize_articles(input_file="processed_articles.json", output_file="final_summaries.json"):
    """
    Reads the processed articles (which contain full text chunks), generates a high-level summary,
    and saves the results to a new JSON file with both the summary and the original chunks.
    """
    with open(input_file, "r", encoding="utf-8") as f:
        articles = json.load(f)

    summarized_articles = []
    for article in articles:
        # Combine all chunks into one full text
        full_text = " ".join(article.get("chunks", []))
        # Generate a high-level extractive summary
        high_level_summary = extractive_summary(full_text, num_sentences=3)
        summarized_articles.append({
            "Title": article.get("Title", ""),
            "url": article.get("url", ""),
            "high_level_summary": high_level_summary,
            "chunks": article.get("chunks", []),
            "entities": article.get("entities", {})  # Optional metadata from NER
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summarized_articles, f, ensure_ascii=False, indent=2)
    print(f"Summarized {len(summarized_articles)} articles. Saved to {output_file}.")

if __name__ == "__main__":
    summarize_articles()
