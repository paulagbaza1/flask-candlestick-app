import os
from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import io
import base64



app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret')

def check_consecutive_candles(df, target_color, threshold):
    count = 0
    notifications = []
    for idx, row in df.iterrows():
        if row['Color'] == target_color:
            count += 1
            if count == threshold:
                notifications.append((target_color, idx, count))
        else:
            count = 0
    return notifications

@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    messages = []
    if request.method == 'POST':
        target_timezone = request.form.get('timezone', 'UTC')
        threshold = int(request.form.get('threshold', 3))
        # Adjust the path as needed.
        data_path = r"candlestick_data.csv"
        data = pd.read_csv(data_path, parse_dates=['Date'], index_col='Date')
        data.index = data.index.tz_localize("UTC").tz_convert(target_timezone)
        data['Color'] = data.apply(lambda row: 'green' if row['Close'] >= row['Open'] else 'red', axis=1)

        green_notifications = check_consecutive_candles(data, 'green', threshold)
        red_notifications = check_consecutive_candles(data, 'red', threshold)
        for notif in green_notifications:
            messages.append(f"Alert: {notif[2]} consecutive green candles detected ending on {notif[1].strftime('%Y-%m-%d %H:%M:%S')}.")
        for notif in red_notifications:
            messages.append(f"Alert: {notif[2]} consecutive red candles detected ending on {notif[1].strftime('%Y-%m-%d %H:%M:%S')}.")

        # Plot the chart
        fig, ax = plt.subplots(figsize=(12, 6))
        candle_body_width = 0.8
        for i, (idx, row) in enumerate(data.iterrows()):
            open_price = row['Open']
            close_price = row['Close']
            lower = min(open_price, close_price)
            height = abs(open_price - close_price)
            color = row['Color']
            ax.add_patch(Rectangle((i, lower), candle_body_width, height, color=color))
            ax.plot([i, i], [row['Low'], row['High']], color='black')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data.index.strftime('%Y-%m-%d %H:%M'), rotation=45)
        ax.set_xlabel(f"Date (Time Zone: {target_timezone})")
        ax.set_ylabel("Price")
        plt.title("Candlestick Chart")
        plt.tight_layout()

        # Save the plot to a PNG image in memory
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        image_url = base64.b64encode(img.getvalue()).decode()
        plt.close(fig)

    return render_template('index.html', image_url=image_url, messages=messages)

if __name__ == '__main__':
    app.run(debug=True)