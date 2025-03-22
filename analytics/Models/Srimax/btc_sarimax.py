import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error, mean_absolute_error

# טען את הנתונים
df = pd.read_csv("C:/Users/USER/Documents/ניצן/לימודים/פרויקט גמר - Cursor Ai/final-project/analytics/Data&Features/btc.csv")

# המרה לתאריך ומיון כרונולוגי
df['close_time'] = pd.to_datetime(df['close_time'])
df = df.sort_values('close_time')
df.set_index('close_time', inplace=True)

# בחירת משתנה מטרה
target = df['close_price'].interpolate()

# בחירת משתנים מסבירים
# דוגמה: sentiment + volume + variance (בהתאם למה שיש בקובץ)
exog_vars = df[['sentiment_avg', 'volume', 'sentiment_variance']].interpolate()

# פיצול ל-train/test
train_size = int(len(df) * 0.8)
y_train, y_test = target[:train_size], target[train_size:]
exog_train, exog_test = exog_vars[:train_size], exog_vars[train_size:]

# בניית המודל
model = SARIMAX(y_train,
                exog=exog_train,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 7),
                enforce_stationarity=False,
                enforce_invertibility=False)

results = model.fit(disp=False)

# חיזוי
forecast = results.predict(start=y_test.index[0],
                           end=y_test.index[-1],
                           exog=exog_test,
                           dynamic=False)

# גרף תחזית
plt.figure(figsize=(10, 5))
plt.plot(y_train.index, y_train, label='Train')
plt.plot(y_test.index, y_test, label='Actual')
plt.plot(y_test.index, forecast, label='Forecast')
plt.title("SARIMAX Bitcoin Forecast (with Sentiment)")
plt.xlabel("Date")
plt.ylabel("Close Price")
plt.legend()
plt.tight_layout()
plt.show()

# מדדי דיוק
mse = mean_squared_error(y_test, forecast)
mae = mean_absolute_error(y_test, forecast)
print(f"Mean Squared Error: {mse:.2f}")
print(f"Mean Absolute Error: {mae:.2f}")
