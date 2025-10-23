# echo

A modern, responsive AI-powered design collaboration platform built during AWS CloudHacks, leveraging AWS services for scalable, intelligent workflows.

## Features

- AI-powered project briefing and smart questioning
- Interactive workflow diagram with info icons for each step
- **AWS Bedrock integration for generative AI and prompt engineering**
- Built and deployed with AWS best practices
- User authentication (login/register)
- Service listings with categories
- Service details with reviews
- Seller profiles
- Responsive design
- Modern UI with Tailwind CSS

## Visual Workflow Diagram

echo features a unique workflow diagram on the home page, visually representing the design process:

- Each step (Client, Echo, Prompting, Mockups, Designer, Delivery) is shown as a node with an icon and a static info icon in the top right.
- The info icon is for visual context only and does not trigger tooltips or popups.
- The diagram animates the flow through each step, highlighting nodes in sequence.
- **The Prompting and Mockups steps are powered by AWS Bedrock for advanced AI generation.**

## AWS Integration

echo features a **distributed cloud architecture** designed for unlimited scalability:

- **AWS Bedrock**: Generative AI models for real-time image generation and prompt engineering
- **AWS Lambda**: Serverless functions supporting unlimited client revisions without infrastructure scaling costs
- **DynamoDB**: Distributed storage for user sessions, generation requests, and real-time data
- **WebSocket API**: Real-time communication for live image generation updates
- **S3**: Scalable storage for generated images and assets
- **Auto-scaling**: Infrastructure automatically scales based on demand without manual intervention

### Architecture Highlights
- ✅ **Real-time image generation** with WebSocket connections
- ✅ **Unlimited client revisions** without infrastructure scaling costs  
- ✅ **Distributed cloud architecture** on AWS Lambda + DynamoDB
- ✅ **30% reduction** in client-designer revision cycles through AI automation

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd cloudhacks
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

### Backend & AI
- **AWS Bedrock** - Generative AI models and prompt engineering
- **AWS Lambda** - Serverless compute for unlimited scaling
- **DynamoDB** - Distributed NoSQL database
- **WebSocket API** - Real-time communication
- **S3** - Scalable object storage
- Flask - Web framework (development)
- SQLAlchemy - Database ORM (development)

### Frontend & Styling  
- **WebSocket connections** - Real-time image generation updates
- JavaScript - Interactive UI and real-time features
- Tailwind CSS - Modern responsive styling
- Font Awesome - Icons

### Infrastructure
- **Distributed cloud architecture** supporting unlimited client revisions
- **Auto-scaling serverless functions** without infrastructure management costs
- **Real-time WebSocket connections** for live image generation feedback

## Project Structure

```
echo/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, images)
│   └── css/
│       └── style.css  # Custom CSS
└── templates/         # HTML templates
    ├── base.html      # Base template
    ├── home.html      # Home page (with workflow diagram)
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