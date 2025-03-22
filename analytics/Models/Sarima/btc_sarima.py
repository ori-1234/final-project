import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

# טען את הנתונים
df = pd.read_csv("C:/Users/USER/Documents/ניצן/לימודים/פרויקט גמר - Cursor Ai/final-project/analytics/Data&Features/btc.csv")

# שמור רק על העמודות הדרושות
df = df[['close_time', 'close_price']].copy()
df['close_time'] = pd.to_datetime(df['close_time'])
df.set_index('close_time', inplace=True)

# אפשר להוריד רעשים אם רוצים:
df = df.asfreq('D')  # שינוי התדירות ליומית (אם הנתונים הם כאלה)

# מילוי ערכים חסרים (אם יש)
df['close_price'] = df['close_price'].interpolate()

# חלוקה ל-train/test
train_size = int(len(df) * 0.8)
train, test = df[:train_size], df[train_size:]

# בניית המודל (הפרמטרים נבחרים ידנית – אפשר לכוון אותם)
model = SARIMAX(train, 
                order=(1, 1, 1),            # (p,d,q)
                seasonal_order=(1, 1, 1, 7) # (P,D,Q,s) – שבועי
               )

results = model.fit(disp=False)

# חיזוי
forecast = results.predict(start=test.index[0], end=test.index[-1], dynamic=False)

# גרף תחזית
plt.figure(figsize=(10,5))
plt.plot(train.index, train['close_price'], label='Train')
plt.plot(test.index, test['close_price'], label='Actual')
plt.plot(test.index, forecast, label='Forecast')
plt.legend()
plt.title('SARIMA Bitcoin Forecast')
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.tight_layout()
plt.show()

# מדדי שגיאה
mse = mean_squared_error(test, forecast)
mae = mean_absolute_error(test, forecast)
print(f"Mean Squared Error: {mse:.2f}")
print(f"Mean Absolute Error: {mae:.2f}")
