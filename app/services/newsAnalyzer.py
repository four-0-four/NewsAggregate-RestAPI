import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

# Ensure necessary NLTK data is downloaded
nltk.download('punkt')
nltk.download('wordnet')

def extract_entities(text, top_n=20):
    # Tokenize and lemmatize the text
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(text)
    words = [lemmatizer.lemmatize(word.lower()) for word in tokens if word.isalpha()]

    # Initialize TF-IDF Vectorizer with custom settings
    # Adjusted ngram_range to capture more phrases, which might be contextually relevant
    vectorizer = TfidfVectorizer(stop_words='english', token_pattern=r'\b[a-zA-Z]{3,}\b', ngram_range=(1,3))
    tfidf_matrix = vectorizer.fit_transform([' '.join(words)])

    # Extract TF-IDF scores for the target text
    feature_array = tfidf_matrix.toarray()[0]
    tfidf_scores = zip(vectorizer.get_feature_names_out(), feature_array)

    # Sort words based on TF-IDF scores
    sorted_words = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)

    # Select top N entities
    return [word for word, score in sorted_words][:top_n]