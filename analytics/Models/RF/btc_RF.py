import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# טעינת הנתונים
df = pd.read_csv("C:/Users/USER/Documents/ניצן/לימודים/פרויקט גמר - Cursor Ai/final-project/analytics/Data&Features/btc.csv")

# הגדרת פיצ'רים
excluded_columns = ["id", "close_time", "open_price", "high_price", "low_price", "close_price", "price_change_indicator"]
feature_columns = [col for col in df.columns if col not in excluded_columns]
X = df[feature_columns].select_dtypes(include=[np.number])

# משתנה מטרה (הזזה מ- [-1, 0, 1] ל- [0, 1, 2])
y = df["price_change_indicator"] + 1

# נרמול הפיצ'רים (לא חובה ל-RF אבל עדיין יכול לעזור)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# פיצול לנתוני אימון ובדיקה
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, shuffle=False)

# בניית מודל Random Forest
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# תחזית
y_pred = model.predict(X_test)

# דוח ביצועים
print(classification_report(y_test, y_pred, target_names=["Down (-1)", "Stable (0)", "Up (+1)"]))

# מטריצת בלבול
cm = confusion_matrix(y_test, y_pred)
labels = ["Down (-1)", "Stable (0)", "Up (+1)"]

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap="Greens", xticklabels=labels, yticklabels=labels)
plt.title("Confusion Matrix - Random Forest")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.show()
