import os
import base64
import requests
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from groq import Groq
import datetime

# Load environment variables from .env file
load_dotenv()

# Fetch environment variables
API_KEY = os.getenv('API_KEY')
POLY_ID = os.getenv('POLY_ID')
SECRET_KEY = os.getenv("SECRET_KEY")
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
AGRO_API_KEY = os.getenv('AGRO_API_KEY')
LAT = os.getenv('LAT')
LON = os.getenv('LON')

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Text for pest and disease information
pest_text = '''Tea mosquito bugs, to get rid of them, spray with neem oil and garlic, use sticky traps, and trap crops like castor. Expect results in 2 to 4 weeks.'''
disease_text = '''Detected Disease: Brown Blight is a fungal disease. To treat it, spray a mix of baking soda and water, and apply organic mulch to keep the soil healthy.'''

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/notifications')
def notification():
    return render_template('notification.html')

@app.route('/get_farming_suggestion', methods=['POST'])
def get_farming_suggestion():
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    farming_suggestion = get_chatbot_response(prompt)
    return jsonify({"suggestion": farming_suggestion})

@app.route('/chatbot', methods=["GET", "POST"])
def chat():
    if request.method == 'POST':
        user_question = request.form['user_question']
        response = get_chatbot_response(user_question)

        if 'history' not in session:
            session['history'] = []
        session['history'].append({'user': user_question, 'bot': response})

        return render_template('chatbot.html', history=session['history'])

    return render_template('chatbot.html', history=session.get('history', []))

def get_chatbot_response(question):
    mess = "You are a professional Farming Agent who knows their field very well. Ensure the answer is accurate and helpful: " + question
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": mess}],
        model="llama3-8b-8192",  # Use the desired model
    )
    return chat_completion.choices[0].message.content

@app.route('/weather-alerts')
def weather_alerts():
    # Fetch weather and forecast data securely using AGRO_API_KEY
    current_weather_url = f"https://api.agromonitoring.com/agro/1.0/weather?lat={LAT}&lon={LON}&appid={AGRO_API_KEY}"
    forecast_url = f"https://api.agromonitoring.com/agro/1.0/weather/forecast?lat={LAT}&lon={LON}&appid={AGRO_API_KEY}"

    current_response = requests.get(current_weather_url)
    forecast_response = requests.get(forecast_url)

    current_weather = current_response.json()
    forecast_weather = forecast_response.json()

    return render_template('weather-alerts.html', current_weather=current_weather, forecast_weather=forecast_weather)

@app.route('/get_weather', methods=['POST'])
def get_weather():
    weather_url = "https://api.agromonitoring.com/agro/1.0/weather"
    soil_url = "http://api.agromonitoring.com/agro/1.0/soil"

    weather_response = requests.get(weather_url, params={"lat": LAT, "lon": LON, "appid": API_KEY})
    soil_response = requests.get(soil_url, params={"polyid": POLY_ID, "appid": API_KEY})

    if weather_response.ok and soil_response.ok:
        return jsonify({
            "weather": weather_response.json(),
            "soil": soil_response.json()
        })
    return jsonify({"error": "Failed to fetch data"}), 500

@app.route('/activity-log')
def activity_log():
    ir_plot_data = base64.b64encode(b"").decode('utf-8')
    distance_plot_data = base64.b64encode(b"").decode('utf-8')
    return render_template('activity-log.html', ir_plot_data=ir_plot_data, distance_plot_data=distance_plot_data)

@app.route('/sensors')
def sensors():
    sensor_data = {
        'distance': 150,
        'irValue': 0,
        'temperature': 28,
        'humidity': 65,
        'motion': 1,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return render_template('sensor.html', sensor_data=sensor_data)

@app.route('/zones')
def zones():
    return render_template('zones.html')

if __name__ == "__main__":
    app.run(debug=True)
