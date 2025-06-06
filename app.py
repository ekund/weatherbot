from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import requests
import numpy as np
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_location_from_ip():
    """Get location information with better error handling"""
    try:
        print("Attempting to get location from IP...")
        response = requests.get('https://ipapi.co/json/', timeout=5)
        print(f"IP API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"IP API error response: {response.text}")
            # Fallback to default coordinates for Brooklyn, NY
            return {
                'city': 'Brooklyn',
                'latitude': 40.6782,
                'longitude': -73.9442
            }
        
        data = response.json()
        if not data.get('latitude') or not data.get('longitude'):
            print("IP API returned incomplete location data")
            # Fallback to default coordinates for Brooklyn, NY
            return {
                'city': 'Brooklyn',
                'latitude': 40.6782,
                'longitude': -73.9442
            }
            
        return {
            'city': data.get('city', 'Brooklyn'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude')
        }
    except Exception as e:
        print(f"Error in get_location_from_ip: {str(e)}")
        # Fallback to default coordinates for Brooklyn, NY
        return {
            'city': 'Brooklyn',
            'latitude': 40.6782,
            'longitude': -73.9442
        }

def get_historical_weather(lat, lon, start_date, end_date):
    """Fetch historical weather data from Open-Meteo API"""
    base_url = "https://archive-api.open-meteo.com/v1/archive"
    
    # Format dates as required by the API
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_str,
        'end_date': end_str,
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,cloudcover_mean',
        'timezone': 'auto'
    }
    
    try:
        print(f"Requesting weather data from Open-Meteo API with params: {params}")
        response = requests.get(base_url, params=params)
        print(f"API Response Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API Error Response: {response.text}")
            return pd.DataFrame()
            
        try:
            data = response.json()
        except ValueError as json_err:
            print(f"Failed to parse JSON response. Response content: {response.text}")
            print(f"JSON parsing error: {str(json_err)}")
            return pd.DataFrame()
            
        if not data or 'daily' not in data:
            print(f"Unexpected API response structure: {data}")
            return pd.DataFrame()
            
        # Create a DataFrame from the daily data
        df = pd.DataFrame({
            'date': pd.to_datetime(data['daily']['time']),
            'temp_max': data['daily']['temperature_2m_max'],
            'temp_min': data['daily']['temperature_2m_min'],
            'precipitation': data['daily']['precipitation_sum'],
            'cloudcover': data['daily']['cloudcover_mean']
        })
        
        # Fill NaN values with appropriate defaults
        df['precipitation'] = df['precipitation'].fillna(0)
        df['cloudcover'] = df['cloudcover'].fillna(0)
        df['temp_max'] = df['temp_max'].fillna(method='ffill')
        df['temp_min'] = df['temp_min'].fillna(method='ffill')
        
        # Calculate average temperature and determine weather conditions
        df['temp'] = (df['temp_max'] + df['temp_min']) / 2
        
        # Determine weather conditions based on precipitation and cloud cover
        conditions = []
        for _, row in df.iterrows():
            if pd.isna(row['precipitation']) or pd.isna(row['cloudcover']):
                conditions.append('Sunny')  # Default condition if data is missing
            elif row['precipitation'] > 5:
                conditions.append('Rainy')
            elif row['precipitation'] > 1:
                conditions.append('Drizzle')
            elif row['cloudcover'] > 75:
                conditions.append('Cloudy')
            elif row['cloudcover'] > 25:
                conditions.append('Partly Cloudy')
            else:
                conditions.append('Sunny')
        
        df['weather_main'] = conditions
        return df
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return pd.DataFrame()

def predict_weather(lat, lon, target_date):
    """Predict weather using historical data and simple statistical analysis"""
    # Get historical data for the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Get historical weather data
    df = get_historical_weather(lat, lon, start_date, end_date)
    
    if df.empty:
        return None, "No historical data available"
    
    # Convert target date to datetime
    target_dt = datetime.strptime(target_date, '%Y-%m-%d')
    
    # Find data from similar dates (same month, nearby days)
    # Create an explicit copy of the filtered data
    similar_dates = df[df['date'].dt.month == target_dt.month].copy()
    
    if len(similar_dates) > 0:
        # Calculate days difference using loc
        similar_dates.loc[:, 'days_diff'] = abs(similar_dates['date'].dt.day - target_dt.day)
        # Sort by days difference and get the closest matches
        similar_dates = similar_dates.nsmallest(5, 'days_diff')
    
    if similar_dates.empty:
        return None, "No similar dates found for prediction"
    
    # Calculate predicted temperature (weighted average of similar dates)
    weights = 1 / (similar_dates['days_diff'] + 1)  # Add 1
    pred_temp = (similar_dates['temp'] * weights).sum() / weights.sum()
    
    # Get the most common weather condition from the similar dates
    pred_condition = similar_dates['weather_main'].mode().iloc[0]
    
    return pred_temp, pred_condition

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/location', methods=['GET'])
def get_location():
    location = get_location_from_ip()
    return jsonify(location)

@app.route('/api/weather', methods=['POST'])
def get_weather():
    try:
        data = request.json
        target_date = data['date']
        
        # Validate and parse the date
        try:
            # Try to parse various date formats
            for date_format in ['%Y-%m-%d', '%B %d,%Y', '%B %d, %Y', '%b %d,%Y', '%b %d, %Y']:
                try:
                    target_dt = datetime.strptime(target_date, date_format)
                    target_date = target_dt.strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
            else:
                return jsonify({'error': 'Invalid date format. Please use YYYY-MM-DD or Month DD, YYYY format'}), 400
        except Exception as e:
            print(f"Date parsing error: {str(e)}")
            return jsonify({'error': 'Invalid date format. Please use YYYY-MM-DD or Month DD, YYYY format'}), 400
        
        # Get location from request data
        location = data.get('location', get_location_from_ip())
        print(f"Location data: {location}")
        
        if not location or not location.get('latitude') or not location.get('longitude'):
            return jsonify({'error': 'Could not detect location'}), 400
        
        temperature, conditions = predict_weather(
            location['latitude'],
            location['longitude'],
            target_date
        )
        
        if temperature is None:
            return jsonify({'error': conditions}), 400
        
        return jsonify({
            'temperature': round(temperature, 1),
            'conditions': conditions,
            'location': location['city']
        })
    except Exception as e:
        print(f"Error in get_weather: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 