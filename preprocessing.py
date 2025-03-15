import json
import re
import spacy
from tqdm import tqdm
from spacy.matcher import Matcher

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Predefined topics and subcategories
predefined_topics = [
    "Approaching", "Attraction", "Conversation", "Dating", "Female Mind",
    "History / Misc.", "Lifestyle", "Mate Choice", "Mindsets",
    "Online Dating", "Relationships", "Seduction", "Sex", "Social Life", "Texting & Phones"
]

subcategories = {
    "Approaching": ["Approach Anxiety", "Approach Invitations", "Approach Momentum", "Girls' Signs of Interest", "Going Out to Approach", "Lifestyle Integration", "Making an Approach", "Opening & Openers", "Rejection", "Where to Find Women", "Whom to Approach"],
    "Attraction": ["Attraction Killers", "Attraction Windows", "Attractive Behaviors", "Attractive Clothing", "Attractive Qualities", "Attractive Vibe"],
    "Conversation": ["Break/Build Rapport", "Conversation Tips", "Deep Conversation", "Emotion", "Example Conversations", "Flirtation & Teases", "Fractionation", "Frames", "Hook Point", "Interruptions", "Persuasion", "Reading People", "Screen & Qualify", "Sexual Topics", "Small Talk", "Storytelling", "Talking to Girls", "Talking to Men", "Women's Tests"],
    "Dating": ["Date Followup", "Date Planning", "Dating Different Girls", "Dating Strategies", "First & Second Dates", "Getting Numbers", "How to Get Dates", "Instant Dates", "Older Women", "Proper Precautions", "Sexual Marketplace", "Younger Women", "Your Place"],
    "Female Mind": ["Female Behaviors", "Female Perspectives", "Female Preferences", "Female Sex Drive", "Girl Types", "Loyalty", "Secret Society", "Ways Differ from Men"],
    "History / Misc.": ["Book Reviews", "Good Habits", "Masculinity", "Reading Lists", "Sexual Philosophy", "Social Commentary", "Social Dynamics"],
    "Lifestyle": ["Bad Habits", "Diet & Weight", "Exercise", "How to Live", "Location"],
    "Mate Choice": ["Assortative Mating", "Mental Aspects", "Signs to Look For", "Vetting", "Women to Avoid", "Women to Choose"],
    "Mindsets": ["Confidence", "Expert Mindsets", "Harmful Mindsets", "Independence", "Introverts/Extroverts", "Meditation/Visualization", "Mental Models", "Motivation", "Proper Focuses", "Responsibility", "Self-Sufficiency"],
    "Online Dating": ["Best Dating Apps", "Dating App Messages", "Dating App Photos", "Dating App Strategy", "Drawbacks to Online"],
    "Relationships": ["Behavior Shaping", "Breaking Up", "Casual", "Children", "Devotion", "Divorce", "Drama", "Early Relationship", "Fidelity / Infidelity", "Get an Ex Back", "Jealousy", "Long-Distance", "Long-Term", "Love", "Marriage", "Monogamy", "Open Relationships", "Polygyny", "Power Dynamics", "Relationship Skills", "Sexual Dynamics"],
    "Seduction": ["Arousal", "Attainability", "Compliance", "Dancing", "Escalation", "Expectations", "Friend Zone", "Game Types", "Girl Thieving", "How to Learn", "Initiating Sex", "Kissing", "Logistics", "Making Girls Chase", "Male Competition", "Momentum", "Movie Examples", "Naturals", "NLP", "Picking Up Women", "Post-Sex Conversion", "Preselection", "Pulling Women Home", "Reports", "Resistance Handling", "Showing Interest", "Social Proof", "Speed / Pace", "Sticking Points", "Threesomes", "Touching Women", "Transitions", "Wingmanning"],
    "Sex": ["Experience Creation", "Oral Sex", "Orgasms", "Positions", "Sexual Dysfunction", "Training Her"],
    "Social Life": ["Avoiding Social Harm", "College / University", "Impression Management", "Keeping Friends", "Making Friends", "Network Building", "Social Behavior", "Social Rules & Norms"],
    "Texting & Phones": ["Calling Girls", "Flakes & Ghosts", "Texting Girls", "Video Messaging"]
}

# Gambit patterns
GAMBIT_PATTERNS = [
    {"label": "GAMBIT", "pattern": [{"LOWER": "negging"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "peacocking"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "kino"}, {"LOWER": "escalation"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "push"}, {"LOWER": "pull"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "future"}, {"LOWER": "projection"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "qualification"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "active"}, {"LOWER": "listening"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "emotional"}, {"LOWER": "intelligence"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "storytelling"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "flirting"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "confidence"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "attraction"}, {"LOWER": "triggers"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "social"}, {"LOWER": "proof"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "scarcity"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "reciprocity"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "preselection"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "opener"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "compliance"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "arousal"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "logistics"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "momentum"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "resistance"}, {"LOWER": "handling"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "social"}, {"LOWER": "circle"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "friend"}, {"LOWER": "zone"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "making"}, {"LOWER": "girls"}, {"LOWER": "chase"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "wingmanning"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "preselection"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "prefacing"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "threesomes"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "touching"}, {"LOWER": "women"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "showing"}, {"LOWER": "interest"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "compliance"}, {"LOWER": "ladder"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "sexual"}, {"LOWER": "tension"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "frame"}, {"LOWER": "control"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "fractionation"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "deep"}, {"LOWER": "rapport"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "hook"}, {"LOWER": "point"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "instant"}, {"LOWER": "dates"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "escalation"}, {"LOWER": "windows"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "approach"}, {"LOWER": "anxiety"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "approach"}, {"LOWER": "momentum"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "girls"}, {"LOWER": "signs"}, {"LOWER": "of"}, {"LOWER": "interest"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "rejection"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "rebuff"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "intrigue"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "where"}, {"LOWER": "to"}, {"LOWER": "find"}, {"LOWER": "women"}]},
    {"label": "GAMBIT", "pattern": [{"LOWER": "whom"}, {"LOWER": "to"}, {"LOWER": "approach"}]}
]

matcher = Matcher(nlp.vocab)
for gambit in GAMBIT_PATTERNS:
    matcher.add(gambit["label"], [gambit["pattern"]])

def clean_text(text):
    """Cleans and normalizes text."""
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces/newlines
    text = text.replace("’", "'").strip()  # Normalize apostrophes and trim
    return text

def extract_entities_and_gambits(text):
    """
    Extract named entities, detect gambits, and assign topics/subcategories.
    """
    doc = nlp(text)
    
    # Extract named entities
    entities = {
        "Persons": list(set(ent.text for ent in doc.ents if ent.label_ == "PERSON")),
        "Organizations": list(set(ent.text for ent in doc.ents if ent.label_ == "ORG")),
        "Locations": list(set(ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"])),
        "Dates": list(set(ent.text for ent in doc.ents if ent.label_ in ["DATE", "TIME"])),
        "Gambits": [],
        "Topics": [],
        "Subcategories": []
    }
    
    # Detect predefined gambits
    matches = matcher(doc)
    for match_id, start, end in matches:
        gambit = doc[start:end].text
        entities["Gambits"].append(gambit)
    
    # Assign topics and subcategories
    for topic, subs in subcategories.items():
        if any(sub.lower() in text.lower() for sub in subs):
            entities["Topics"].append(topic)
            entities["Subcategories"].extend(sub for sub in subs if sub.lower() in text.lower())
    
    # Deduplicate lists
    entities["Gambits"] = list(set(entities["Gambits"]))
    entities["Topics"] = list(set(entities["Topics"]))
    entities["Subcategories"] = list(set(entities["Subcategories"]))
    
    return entities

def split_into_semantic_chunks(text, max_tokens=300):
    """Split text into chunks based on sentence boundaries and relevance."""
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
    """Load, clean, and process articles with NER, gambit detection, and topic tagging."""
    with open(input_file, "r", encoding="utf-8") as f:
        articles = json.load(f)

    processed_articles = []

    for article in tqdm(articles, desc="Processing articles"):
        title = clean_text(article.get("Title", "No Title"))
        url = article.get("url", "")
        content = clean_text(article.get("content", ""))
        
        # Extract entities, gambits, and topics
        entities = extract_entities_and_gambits(content)
        
        # Create semantic chunks
        chunks = split_into_semantic_chunks(content)

        # Append processed data
        processed_articles.append({
            "Title": title,
            "url": url,
            "chunks": chunks,
            "entities": entities,
        })

    # Save processed articles to output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_articles, f, ensure_ascii=False, indent=2)

    print(f"Processed {len(processed_articles)} articles. Saved to {output_file}.")

if __name__ == "__main__":
    preprocess_articles()
