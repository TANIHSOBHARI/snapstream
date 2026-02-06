from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Training dataset
titles = [
    "python tutorial",
    "machine learning basics",
    "data science project",
    "football match highlights",
    "cricket world cup",
    "sports training session",
    "movie trailer",
    "funny comedy video",
    "music concert live",
    "technology review",
    "latest gadgets",
    "programming tips"
]

categories = [
    "Education",
    "Education",
    "Education",
    "Sports",
    "Sports",
    "Sports",
    "Entertainment",
    "Entertainment",
    "Entertainment",
    "Technology",
    "Technology",
    "Technology"
]

# Train ML model
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(titles)

model = MultinomialNB()
model.fit(X, categories)

def predict_category(title):
    title_vector = vectorizer.transform([title.lower()])
    return model.predict(title_vector)[0]
