# MDX-CST4160
MDX Dubai - MSc Fintech - CST4160 Advanced Software Development for Financial Technology

# Crypto Price Tracker Application

A real-time cryptocurrency price tracking application with watchlist functionality and crypto news integration.

## Features

- **Live Price Ticker**: Scrolling display of top 10 cryptocurrencies by market cap
- **Personal Watchlist**: Track your favorite cryptocurrencies with price and 24h change
- **News Integration**: Latest cryptocurrency news from multiple sources
- **User Preferences**: Save your preferred cryptocurrencies between sessions

## Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript, Jinja2 templating
- **Backend**: Python, Flask
- **APIs**: Binance API (prices), NewsAPI, Guardian API
- **Database**: SQLite
- **Dependencies**: 
  - `flask` (web framework)
  - `python-binance` (Binance API client)
  - `requests` (API calls)
  - `werkzeug` (security and authentication)

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip package manager
- API keys for:
  - Binance (for price data)
  - NewsAPI (optional)
  - The Guardian (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ScottSanders2/MDX-CST4160.git
   cd crypto_price_app_v5

### Create and activate a virtual environment:

- python -m venv venv
#### Windows:
- venv\Scripts\activate
#### macOS/Linux:
- source venv/bin/activate

### Install dependencies:

- pip install -r requirements

## Running the Application

### Start the development server:

python app_v4.1.py

### The application will be available at:

http://localhost:5002

## Usage

### Login: Use one of the default accounts or register a new one

- Scott / password1
- Georgii / password2
- Ayushman / password3
- Kunal / password4

### Watchlist:

- View your selected cryptocurrencies in the sidebar
- Prices update automatically every 5 seconds

### Preferences:

- Select/deselect cryptocurrencies to track
- Click "Save Preferences" to update your watchlist

### News:

- View the latest cryptocurrency news in the main content area
- Articles open in a new tab when clicked

## File Structure
<img width="514" alt="image" src="https://github.com/user-attachments/assets/7cd9482f-09ab-4e4c-ad05-07ae5df22e8e" />

## API Endpoints
<img width="601" alt="image" src="https://github.com/user-attachments/assets/e197cd6e-4167-4efa-ba43-3e7b34d3bb9b" />

## Configuration Options
The application can be configured by editing app_v4.1.py:

- **UPDATE_INTERVAL:** How often to refresh top 10 cryptos (seconds)
- **DEFAULT_USERS:** Pre-configured user accounts
- **DEFAULT_PREFS:** Default cryptocurrency preferences

## Troubleshooting

- Issue: Unable to run 'app_v4.1.py' - various errors
  - Check that your Python Interpreter is pointing at the 'venv' virtual environment in the version of the app that you are trying to run
  - Conflicts with 'venv' working directory can result in issues runing the application, such as 'binance.spot' not installing correctly
  - Ensure that all requirements are loaded in the .venv virtual environment of the version of the application you are running

- Issue: Prices not updating
  - Verify your Binance API keys are correct
  - Check your internet connection
  - Ensure the Flask server is running without errors

- Issue: News not loading
  - Verify your NewsAPI and Guardian API keys
  - Check the console for API errors
  - Some news sources may have rate limits

- Issue: Database problems
  - Delete crypto_tracker.db and restart the application
  - Check file permissions in the project directory

- Contributing - when contributing, please follow these steps:
  - Fork the repository
  - Create a feature branch (git checkout -b feature/your-feature)
  - Commit your changes (git commit -am 'Add some feature')
  - Push to the branch (git push origin feature/your-feature)
  - Open a Pull Request

- License
  - This project is licensed under the MIT License - see the LICENSE file for details.

- Acknowledgments
  - Binance for the cryptocurrency price API
  - NewsAPI.org for news content
  - The Guardian for additional news content
  - Flask community for the web framework
