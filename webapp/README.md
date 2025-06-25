# Spotify Listener Tracker

This project is a Flask web application designed to explore and track changes in monthly listeners for various artists based on data stored in a JSON file.

## Features

- Search for artists by name.
- Display relevant records including monthly listeners.
- Track changes in monthly listeners as new data becomes available.

## Project Structure

```
spotify-listener-tracker
├── app
│   ├── __init__.py
│   ├── routes.py
│   ├── static
│   ├── templates
│   │   └── index.html
│   └── utils.py
├── data
│   └── listeners.json
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd spotify-listener-tracker
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python -m app
   ```

4. Open your web browser and go to `http://127.0.0.1:5000` to access the application.

## Usage

- Use the search bar on the home page to enter the name of an artist.
- The application will display the relevant records, including the number of monthly listeners for the searched artist.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License.