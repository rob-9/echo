from app import create_app
import os

# Create Flask app instance for Vercel
app = create_app(config_name='production' if os.environ.get('VERCEL') else 'development')

# For Vercel deployment
handler = app

if __name__ == "__main__":
    app.run()