# FiverrClone

A modern, responsive Fiverr-like marketplace built with Flask and Tailwind CSS.

## Features

- User authentication (login/register)
- Service listings with categories
- Service details with reviews
- Seller profiles
- Responsive design
- Modern UI with Tailwind CSS

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd fiverr-clone
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

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the development server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Technologies Used

- Flask - Web framework
- SQLAlchemy - Database ORM
- Tailwind CSS - Styling
- Font Awesome - Icons
- SQLite - Database

## Project Structure

```
fiverr-clone/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, images)
│   └── css/
│       └── style.css  # Custom CSS
└── templates/         # HTML templates
    ├── base.html      # Base template
    ├── home.html      # Home page
    ├── login.html     # Login page
    ├── register.html  # Registration page
    ├── services.html  # Services listing
    └── service_detail.html  # Service details
```

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.