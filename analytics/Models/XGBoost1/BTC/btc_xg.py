import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import seaborn as sns

# 1. טעינת הנתונים
file_path = r"C:\Users\USER\Documents\ניצן\לימודים\פרויקט גמר - Cursor Ai\final-project\analytics\Data&Features\btc.csv"

df = pd.read_csv(file_path)

# 2. בחירת הפיצ'רים (מדדים בלבד, לא תאריך/ID/מחירים)
excluded_columns = ["id", "close_time", "open_price", "high_price", "low_price", "close_price", "price_change_indicator"]
feature_columns = [col for col in df.columns if col not in excluded_columns]
features = df[feature_columns].select_dtypes(include=[np.number])

# 3. משתנה מטרה (שינוי → קטגוריות 0, 1, 2)
target = df["price_change_indicator"] + 1  # -1 ➝ 0, 0 ➝ 1, 1 ➝ 2

# 4. נרמול הפיצ'רים
scaler = MinMaxScaler()
X = scaler.fit_transform(features)
y = target

# 5. חלוקה כרונולוגית ל־60/20/20
train_size = int(0.6 * len(X))
val_size = int(0.8 * len(X))
X_train, X_val, X_test = X[:train_size], X[train_size:val_size], X[val_size:]
y_train, y_val, y_test = y[:train_size], y[train_size:val_size], y[val_size:]

model = XGBClassifier(
    objective="multi:softmax",
    num_class=3,
    eval_metric="mlogloss",
    use_label_encoder=False,
    random_state=42,
    subsample=0.8,
    colsample_bytree=0.8
)

model.fit(X_train, y_train)

# 7. חיזוי וביצועים
y_pred = model.predict(X_test)
report = classification_report(y_test, y_pred, target_names=["Down (-1)", "Stable (0)", "Up (+1)"])
print(report)

# 8. מטריצת בלבול
cm = confusion_matrix(y_test, y_pred)
labels = ["Down (-1)", "Stable (0)", "Up (+1)"]
print("Confusion Matrix:\n", pd.DataFrame(cm, index=labels, columns=labels))

plt.figure(figsize=(6,5))
sns.heatmap(cm, annot=True, fmt='d', cmap="Blues", xticklabels=labels, yticklabels=labels)
plt.title("Confusion Matrix - XGBoost")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.show()

# 9. חשיבות הפיצ'רים
plt.figure(figsize=(10, 6))
xgb_features = model.feature_importances_
sorted_idx = np.argsort(xgb_features)
plt.barh(np.array(feature_columns)[sorted_idx], xgb_features[sorted_idx])
plt.title("Feature Importance (XGBoost)")
plt.xlabel("Importance")
plt.tight_layout()
plt.show()
