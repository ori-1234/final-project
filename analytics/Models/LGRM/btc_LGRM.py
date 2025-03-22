import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# טעינת הנתונים
df = pd.read_csv("C:/Users/USER/Documents/ניצן/לימודים/פרויקט גמר - Cursor Ai/final-project/analytics/Data&Features/btc.csv")

# הסרת עמודות שלא רלוונטיות לפיצ'רים
excluded_columns = ["id", "close_time", "open_price", "high_price", "low_price", "close_price", "price_change_indicator"]
feature_columns = [col for col in df.columns if col not in excluded_columns]

# שמירה רק על פיצ'רים מספריים
X = df[feature_columns].select_dtypes(include=[np.number])

# משתנה מטרה (הזזה מ- [-1, 0, 1] ל- [0, 1, 2])
y = df["price_change_indicator"] + 1

# נרמול הפיצ'רים
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# פיצול לנתוני אימון ובדיקה
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, shuffle=False)

# בניית מודל Logistic Regression
model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000)
model.fit(X_train, y_train)

# תחזית על סט הבדיקה
y_pred = model.predict(X_test)

# --- מטריצת בלבול ---
cm = confusion_matrix(y_test, y_pred)
labels = ["Down (-1)", "Stable (0)", "Up (+1)"]

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap="Purples", xticklabels=labels, yticklabels=labels)
plt.title("Confusion Matrix - Logistic Regression")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.show()

# --- דוח ביצועים גרפי ---
report_dict = classification_report(y_test, y_pred, output_dict=True, target_names=labels)
report_df = pd.DataFrame(report_dict).T.loc[labels, ["precision", "recall", "f1-score"]]

report_df.plot(kind='bar', figsize=(8, 6))
plt.title("Classification Metrics by Class - Logistic Regression")
plt.ylabel("Score")
plt.ylim(0, 1.05)
plt.xticks(rotation=0)
plt.legend(loc='lower right')
plt.tight_layout()
plt.show()

# --- חשיבות פיצ'רים לפי Coefficients ---
coefficients = model.coef_  # צורת המטריצה היא (n_classes, n_features)
mean_abs_coef = np.mean(np.abs(coefficients), axis=0)  # ממוצע מוחלט בין הקלאסים
feature_names = X.columns

# מיון פיצ'רים לפי גודל
sorted_idx = np.argsort(mean_abs_coef)[::-1]

plt.figure(figsize=(10, 6))
sns.barplot(x=mean_abs_coef[sorted_idx], y=feature_names[sorted_idx], palette="coolwarm")
plt.title("Feature Importance (Coefficient Magnitude) - Logistic Regression")
plt.xlabel("Average Absolute Coefficient")
plt.ylabel("Feature")
plt.tight_layout()
plt.show()
