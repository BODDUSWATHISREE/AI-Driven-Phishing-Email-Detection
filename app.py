from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import joblib
import pandas as pd
import re
import string
import nltk
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from scipy.sparse import hstack

app = FastAPI(title="AI-Driven Phishing Email Detection")

# -----------------------------
# Static & Templates
# -----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# -----------------------------
# NLTK
# -----------------------------
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("omw-1.4")

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# -----------------------------
# Load Model
# -----------------------------
model = joblib.load("phishing_model.pkl")
tfidf = joblib.load("tfidf_vectorizer.pkl")


class EmailRequest(BaseModel):
    email: str


# -----------------------------
# Email Cleaning
# -----------------------------
def clean_email(text):

    text = str(text)

    text = BeautifulSoup(text, "html.parser").get_text()

    text = re.sub(r"http\S+|www\S+", " ", text)

    text = text.lower()

    text = text.translate(str.maketrans("", "", string.punctuation))

    text = re.sub(r"\d+", " ", text)

    text = re.sub(r"\s+", " ", text).strip()

    words = text.split()

    words = [w for w in words if w not in stop_words]

    words = [lemmatizer.lemmatize(w) for w in words]

    return " ".join(words)


# -----------------------------
# Metadata
# -----------------------------
def extract_metadata(text):

    email_length = len(text)

    url_count = len(re.findall(r"http[s]?://|www\.", text))

    digit_count = sum(c.isdigit() for c in text)

    uppercase_count = sum(c.isupper() for c in text)

    exclamation_count = text.count("!")

    special_char_count = len(re.findall(r"[^\w\s]", text))

    return pd.DataFrame(
        [[
            email_length,
            url_count,
            digit_count,
            uppercase_count,
            exclamation_count,
            special_char_count
        ]],
        columns=[
            "email_length",
            "url_count",
            "digit_count",
            "uppercase_count",
            "exclamation_count",
            "special_char_count"
        ]
    )


# -----------------------------
# Home Page
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


# -----------------------------
# Prediction
# -----------------------------
@app.post("/predict")
async def predict(data: EmailRequest):
    try:
        if not data.email.strip():
            raise HTTPException(
                status_code=400,
                detail="Email cannot be empty."
            )

        cleaned = clean_email(data.email)
        text_features = tfidf.transform([cleaned])
        metadata = extract_metadata(data.email)
        final_features = hstack([text_features, metadata.values])

        prediction = model.predict(final_features)[0]
        probability = float(model.predict_proba(final_features)[0][1])

        return {
            "prediction": "Phishing" if prediction == 1 else "Legitimate",
            "probability": probability
        }

    except Exception as e:
        print("Prediction Error:", e)
        raise HTTPException(
            status_code=500,
            detail="Prediction failed."
        )