import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt

# טען את הנתונים
df = pd.read_csv("C:/Users/USER/Documents/ניצן/לימודים/פרויקט גמר - Cursor Ai/final-project/analytics/Data&Features/btc.csv")

# שמירה רק על תאריך ומחיר סגירה
df = df[['close_time', 'close_price']].copy()
df.rename(columns={'close_time': 'ds', 'close_price': 'y'}, inplace=True)

# המרת עמודת זמן לפורמט datetime
df['ds'] = pd.to_datetime(df['ds'])

# יצירת המודל
model = Prophet(daily_seasonality=True)

# אימון המודל
model.fit(df)

# יצירת תחזית ל-30 ימים קדימה
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

# הצגת גרף תחזית
model.plot(forecast)
plt.title("Bitcoin Price Forecast")
plt.xlabel("Date")
plt.ylabel("Close Price")
plt.tight_layout()
plt.show()

# שמירת תחזית לקובץ
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv("btc_forecast.csv", index=False)
print("✅ התחזית נשמרה כ-btc_forecast.csv")
