document.addEventListener('DOMContentLoaded', async function() {
    // Get user's location
    let userLocation = null;
    try {
        const response = await fetch('/api/location');
        userLocation = await response.json();
        // Update location display
        document.querySelector('.location-display p').textContent = userLocation.city;
    } catch (error) {
        console.error('Error fetching location:', error);
        document.querySelector('.location-display p').textContent = 'Location not available';
    }

    // Initialize date picker
    const datePicker = flatpickr("#date", {
        minDate: "today",
        maxDate: new Date().fp_incr(30), // Limit to 30 days in advance
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "F j, Y",
        disableMobile: "true"
    });

    // Weather condition icons mapping
    const weatherIcons = {
        'Sunny': 'https://cdn-icons-png.flaticon.com/512/869/869869.png',
        'Cloudy': 'https://cdn-icons-png.flaticon.com/512/414/414927.png',
        'Rainy': 'https://cdn-icons-png.flaticon.com/512/3351/3351979.png',
        'Stormy': 'https://cdn-icons-png.flaticon.com/512/3351/3351979.png',
        'Snowy': 'https://cdn-icons-png.flaticon.com/512/642/642102.png'
    };

    let currentTemperature = null;

    // Temperature conversion functions
    function celsiusToFahrenheit(celsius) {
        return (celsius * 9/5) + 32;
    }

    function formatTemperature(temp, unit) {
        return `${Math.round(unit === 'F' ? celsiusToFahrenheit(temp) : temp)}°${unit}`;
    }

    // Handle temperature unit change
    document.querySelectorAll('input[name="temp-unit"]').forEach(radio => {
        radio.addEventListener('change', function() {
            if (currentTemperature !== null) {
                document.querySelector('.temperature').textContent = 
                    formatTemperature(currentTemperature, this.value);
            }
        });
    });

    // Handle prediction button click
    document.getElementById('predict-button').addEventListener('click', async function() {
        const date = document.getElementById('date').value;
        const selectedUnit = document.querySelector('input[name="temp-unit"]:checked').value;
        
        if (!date) {
            alert('Please select a date first!');
            return;
        }

        if (!userLocation) {
            alert('Location data not available. Please try again later.');
            return;
        }

        try {
            const response = await fetch('/api/weather', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    date: date,
                    location: userLocation
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to get weather prediction');
            }
            
            currentTemperature = data.temperature;
            
            // Update the weather result display
            const resultDiv = document.querySelector('.weather-result');
            document.getElementById('weather-icon').src = weatherIcons[data.conditions] || weatherIcons['Sunny'];
            document.querySelector('.temperature').textContent = formatTemperature(currentTemperature, selectedUnit);
            document.querySelector('.conditions').textContent = data.conditions;
            document.querySelector('.location').textContent = data.location;
            
            resultDiv.style.display = 'block';
            
            // Smooth scroll to results
            resultDiv.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'Failed to get weather prediction. Please try again.');
        }
    });
}); 