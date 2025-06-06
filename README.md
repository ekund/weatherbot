# WeatherBot

A Flask-based weather prediction application that uses historical data to forecast weather conditions.

## Features

- Weather prediction based on historical data
- Temperature display in both Celsius and Fahrenheit
- Location-based forecasting
- Modern, responsive UI with Bootstrap
- Date picker with one-month limit
- Weather condition icons

## Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd weatherbot
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5001`

## Deployment on Render

This application is configured for easy deployment on Render.com's free tier:

1. Create a [Render account](https://render.com)

2. Fork or push this repository to your GitHub account

3. In Render Dashboard:
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repository
   - Name your service (e.g., "weatherbot")
   - Select "Python" as the environment
   - The following settings will be automatically configured from render.yaml:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app`

4. Set up environment variables in Render Dashboard:
   - Go to your web service dashboard
   - Click on "Environment"
   - Add the following secret variables:
     - `SECRET_KEY`: Click "Generate" for a secure random value
     - `DATABASE_URL`: `sqlite:///weather.db`

5. Click "Create Web Service"

Your application will be deployed and available at `https://your-service-name.onrender.com`

## Environment Variables

The application uses two types of environment variables:

### Non-sensitive variables (configured in render.yaml):
- `PORT`: 5001
- `PYTHON_VERSION`: 3.11.0

### Sensitive variables (set in Render Dashboard):
- `SECRET_KEY`: Used for Flask session security
- `DATABASE_URL`: Database connection string

To modify environment variables:
1. For non-sensitive variables: Edit `render.yaml`
2. For sensitive variables: Use the Render Dashboard
   - Go to your service in Render
   - Click "Environment"
   - Add or modify variables as needed
   - Click "Save Changes" to apply

## Technologies Used

- Flask
- SQLAlchemy
- Bootstrap 5
- Flatpickr
- Open-Meteo API
- Python 3.11

