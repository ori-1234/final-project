import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout, Input
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
import seaborn as sns
import matplotlib.pyplot as plt

# 1. טעינת הנתונים
file_path = r"C:\Users\USER\Documents\ניצן\לימודים\פרויקט גמר - Cursor Ai\final-project\analytics\Data&Features\btc.csv"

df = pd.read_csv(file_path)

# 2. הגדרת עמודות פיצ'רים: הסרת מזהים, תאריכים, מחירים, ומשתנה מטרה
excluded_columns = ["id", "close_time", "open_price", "high_price", "low_price", "close_price", "price_change_indicator"]
feature_columns = [col for col in df.columns if col not in excluded_columns]

# 3. שמירה רק על פיצ'רים מספריים
features = df[feature_columns].select_dtypes(include=[np.number])

# 4. משתנה מטרה (עם שינוי לקטגוריות: -1 → 0, 0 → 1, 1 → 2)
target = df["price_change_indicator"] + 1

# 5. נרמול פיצ'רים בלבד
scaler_X = MinMaxScaler()
X = scaler_X.fit_transform(features)

# 6. יצירת רצפים של טיימסטפים (10 דקות אחורה)
def create_sequences(X, y, time_steps=10):
    Xs, ys = [], []
    for i in range(time_steps, len(X)):
        Xs.append(X[i-time_steps:i])
        ys.append(y[i])
    return np.array(Xs), np.array(ys)

time_steps = 10
X_seq, y_seq = create_sequences(X, target, time_steps)
y_cat = to_categorical(y_seq, num_classes=3)

# 7. פיצול כרונולוגי
train_size = int(0.6 * len(X_seq))
val_size = int(0.8 * len(X_seq))
X_train, X_val, X_test = X_seq[:train_size], X_seq[train_size:val_size], X_seq[val_size:]
y_train, y_val, y_test = y_cat[:train_size], y_cat[train_size:val_size], y_cat[val_size:]
y_train_labels = y_seq[:train_size]
y_true_classes = y_seq[val_size:]

# 8. חישוב class weights
class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y_train_labels), y=y_train_labels)
class_weight_dict = dict(enumerate(class_weights))

# 9. בניית המודל
model = Sequential([
    Input(shape=(time_steps, X_train.shape[2])),
    LSTM(64, return_sequences=True),
    Dropout(0.3),
    LSTM(32),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dense(3, activation='softmax')
])

# 10. קימפול המודל
model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])

# 11. אימון המודל עם EarlyStopping
early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=50,
    batch_size=32,
    class_weight=class_weight_dict,
    callbacks=[early_stop],
    verbose=1
)

# 12. חיזוי והערכת ביצועים
y_pred = model.predict(X_test)
y_pred_classes = np.argmax(y_pred, axis=1)

# 13. דוח ביצועים
report = classification_report(y_true_classes, y_pred_classes, target_names=["Down (-1)", "Stable (0)", "Up (+1)"])
print(report)

# 14. Confusion Matrix
cm = confusion_matrix(y_true_classes, y_pred_classes)
labels = ["Down (-1)", "Stable (0)", "Up (+1)"]

print("\nConfusion Matrix:")
print(pd.DataFrame(cm, index=labels, columns=labels))

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap="Blues", xticklabels=labels, yticklabels=labels)
plt.title("Confusion Matrix")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.tight_layout()
plt.show()
