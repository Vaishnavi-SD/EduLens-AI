// Declare variables
const apiKey = 'YOUR_API_KEY'; // Replace with your OpenWeatherMap API key
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const weatherDisplay = document.getElementById('weatherDisplay');
const historyDisplay = document.getElementById('historyDisplay');

// Function to fetch weather data
function fetchWeather(city) {
    fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`)
        .then(response => response.json())
        .then(data => {
            if (data.cod === 200) {
                displayWeather(data);
                updateHistory(city);
            } else {
                alert(data.message);
            }
        });
}

// Display weather data
function displayWeather(data) {
    const weatherHtml = `
        <h2>${data.name}</h2>
        <p>Temperature: ${data.main.temp} °C</p>
        <p>Weather: ${data.weather[0].description}</p>
    `;
    weatherDisplay.innerHTML = weatherHtml;
}

// Function to update search history
function updateHistory(city) {
    let history = JSON.parse(localStorage.getItem('searchHistory')) || [];
    if (!history.includes(city)) {
        history.push(city);
        localStorage.setItem('searchHistory', JSON.stringify(history));
    }
    displayHistory();
}

// Display search history
function displayHistory() {
    let history = JSON.parse(localStorage.getItem('searchHistory')) || [];
    historyDisplay.innerHTML = history.map(city => `<li>${city}</li>`).join('');
}

// Event listeners
searchButton.addEventListener('click', () => {
    const city = searchInput.value;
    fetchWeather(city);
});

// Geolocation function
function getGeolocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const { latitude, longitude } = position.coords;
            fetchWeatherByCoordinates(latitude, longitude);
        });
    }
}

// Fetch weather using geolocation
function fetchWeatherByCoordinates(lat, lon) {
    fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${apiKey}&units=metric`)
        .then(response => response.json())
        .then(data => displayWeather(data));
}

// Initialize search history display
displayHistory();
getGeolocation();