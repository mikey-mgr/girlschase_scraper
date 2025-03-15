from transformers import pipeline

def download_distilbart_cnn():
    """Downloads the distilbart-cnn-12-6 model to the local cache."""
    try:
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        print("distilbart-cnn-12-6 model downloaded successfully!")
    except Exception as e:
        print(f"Error downloading model: {e}")

if __name__ == "__main__":
    download_distilbart_cnn()

    