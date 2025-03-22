import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 1. טעינת הנתונים
file_path = r"C:\Users\USER\Documents\ניצן\לימודים\פרויקט גמר - Cursor Ai\final-project\analytics\Data&Features\btc.csv"

df = pd.read_csv(file_path)

# 2. בחירת משתנה המטרה - מחירי הסגירה של ביטקוין (או כל מדד אחר שאתה רוצה לחזות)
df['close_time'] = pd.to_datetime(df['close_time'])  # המרת עמודת הזמן לפורמט תאריך
df.set_index('close_time', inplace=True)  # קביעת העמודה כמדד זמן
df = df.sort_index()  # מיון כרונולוגי

# 3. בחירת הנתון לחיזוי - כאן מחיר הסגירה
target_column = "close_price"  # אפשר לשנות לכל מדד אחר שרוצים לחזות
data = df[target_column]

# 4. חלוקה לסט אימון (80%) וסט בדיקה (20%)
train_size = int(len(data) * 0.8)
train, test = data[:train_size], data[train_size:]

# 5. התאמת מודל ARIMA
p, d, q = 5, 1, 2  # ערכים התחלתיים (ניתן לבצע כיוונון בהמשך)
model = ARIMA(train, order=(p, d, q))
model_fit = model.fit()

# 6. תחזית על סט הבדיקה
forecast = model_fit.forecast(steps=len(test))
test_index = test.index

# 7. חישוב שגיאות
mae = mean_absolute_error(test, forecast)
mse = mean_squared_error(test, forecast)
rmse = np.sqrt(mse)

print(f"📊 Model Evaluation:")
print(f"🔹 MAE: {mae:.2f}")
print(f"🔹 MSE: {mse:.2f}")
print(f"🔹 RMSE: {rmse:.2f}")


# 8. גרף השוואה בין הערכים האמיתיים לתחזיות
plt.figure(figsize=(10,5))
plt.plot(train.index, train, label="Training Data")
plt.plot(test_index, test, label="Actual Prices", color="blue")
plt.plot(test_index, forecast, label="ARIMA Forecast", color="red", linestyle="dashed")
plt.xlabel("Date")
plt.ylabel("Price")
plt.title(f"ARIMA Forecast for {target_column}")
plt.legend()
plt.grid()
plt.show()
