import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# שם המודל
model_name = "ElKulako/cryptobert"

# טעינת המודל וה-tokenizer
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# הגדרת pipeline לניתוח סנטימנט
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model,
    tokenizer=tokenizer,
    device=0 if torch.cuda.is_available() else -1
)



# טעינת הנתונים מהקובץ שהעלית
df = pd.read_csv("/mnt/data/Reddit_data.csv")  # עדכן את שם הקובץ לפי הצורך

# בדיקה שהעמודה text קיימת
if "text" not in df.columns:
    raise ValueError("העמודה 'text' לא נמצאה בנתונים!")

# הפעלת המודל על כל הטקסטים
df["sentiment"] = df["text"].apply(lambda x: sentiment_pipeline(x)[0]['label'])
df["sentiment_score"] = df["text"].apply(lambda x: sentiment_pipeline(x)[0]['score'])

# הצגת התוצאות הראשונות
print(df[["text", "sentiment", "sentiment_score"]].head())

# שמירת התוצאות לקובץ חדש
df.to_csv("/mnt/data/Reddit_Sentiment_Analysis.csv", index=False)