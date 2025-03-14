import json
import re
import spacy
from tqdm import tqdm

# Load SpaCy model (use "en_core_web_sm" or "en_core_web_trf" for better accuracy)
nlp = spacy.load("en_core_web_sm")

def clean_text(text):
    """Basic text preprocessing: remove extra whitespace, normalize punctuation."""
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces/newlines
    text = text.replace("’", "'")  # Normalize apostrophes
    text = text.strip()
    return text

def extract_entities(text):
    """Extract named entities (People, Organizations, Locations, Dates, etc.)."""
    doc = nlp(text)
    entities = {
        "Persons": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
        "Organizations": [ent.text for ent in doc.ents if ent.label_ == "ORG"],
        "Locations": [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]],
        "Dates": [ent.text for ent in doc.ents if ent.label_ in ["DATE", "TIME"]],
    }
    return entities

def split_into_chunks(text, max_tokens=300):
    """Split long articles into chunks while keeping sentences intact."""
    doc = nlp(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sent in doc.sents:
        sent_length = len(sent.text.split())
        if current_length + sent_length > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(sent.text)
        current_length += sent_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def preprocess_articles(input_file="articles.json", output_file="processed_articles.json"):
    """Load, clean, and process articles with NER and chunking."""
    with open(input_file, "r", encoding="utf-8") as f:
        articles = json.load(f)

    processed_articles = []

    for article in tqdm(articles, desc="Processing articles"):
        title = clean_text(article.get("Title", "No Title"))
        url = article.get("url", "")
        content = clean_text(article.get("content", ""))
        
        entities = extract_entities(content)
        chunks = split_into_chunks(content)

        processed_articles.append({
            "Title": title,
            "url": url,
            "chunks": chunks,
            "entities": entities,
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_articles, f, ensure_ascii=False, indent=2)

    print(f"Processed {len(processed_articles)} articles. Saved to {output_file}.")

if __name__ == "__main__":
    preprocess_articles()