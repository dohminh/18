# Personal Finance Management Web Application

A comprehensive personal finance management application built with Python Flask and Docker. This application helps users track their income, expenses, savings, and financial goals with an intuitive interface and powerful analytics.

## Features

### Financial Tracking
- Track income, expenses, and savings
- Categorize transactions
- Support for multiple payment methods
- Account payable and receivable tracking
- Monthly and yearly financial summaries

### Budget Management
- Set monthly budgets by category
- Track budget vs. actual spending
- Visual budget progress indicators
- Budget recommendations based on spending patterns

### Savings Goals
- Create and track multiple savings goals
- Set target amounts and deadlines
- Track progress towards goals
- Automatic savings calculations

### Analytics & Reporting
- Interactive dashboard with financial overview
- Monthly income vs. expense charts
- Category-wise expense breakdown
- 6-month financial trend analysis
- Net cash flow calculations

### User Management
- Secure user authentication
- User profile management
- Test account creation for demo purposes
- Role-based access control

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /signup` - New user registration
- `GET /logout` - User logout

### Dashboard
- `GET /` or `GET /dashboard` - Main dashboard view
- `GET /cashflows` - View all transactions
- `GET /outstanding` - View pending payments

### Transactions
- `POST /add-cashflow` - Add new transaction
- `POST /edit-cashflow` - Edit existing transaction
- `POST /delete-cashflow` - Delete transaction

### Budget Management
- `GET /budget` - View and manage budgets
- `POST /budget` - Update budget settings

### Savings Goals
- `GET /saving-goals` - View all savings goals
- `POST /add-saving-goal` - Create new savings goal
- `POST /edit-saving-goal` - Edit existing goal
- `POST /delete-saving-goal` - Delete savings goal

### Testing & Development
- `GET /create-test-account` - Create test user account
- `GET /stress-test` - Run application stress tests

## Technologies Used

### Backend
- **Framework**: Flask 2.3.3
- **Database ORM**: SQLAlchemy 2.0.21
- **Authentication**: Flask-Login 0.6.2
- **Data Validation**: Pydantic 2.4.2
- **Date Handling**: python-dateutil 2.8.2

### Frontend
- HTML5, CSS3, JavaScript
- Chart.js for data visualization
- Bootstrap for responsive design

### Infrastructure
- **Database**: SQLite (development) / PostgreSQL (production)
- **Containerization**: Docker & Docker Compose
- **Version Control**: Git

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Git
- pip (Python package manager)
- Modern web browser

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd webapp15
```

2. Set up virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Using Docker

1. Build and start the containers:
```bash
docker-compose up --build
```

2. The application will be available at `http://localhost:5000`

### Running Locally

1. Activate the virtual environment:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Run the application:
```bash
python main.py
```

3. The development server will start at `http://localhost:5000`

## Project Structure

```
webapp15/
├── app/                    # Application code
│   ├── __init__.py        # Application factory
│   ├── models.py          # Database models
│   ├── views.py           # Route handlers and views
│   ├── auth.py            # Authentication logic
│   ├── modules/           # Business logic modules
│   ├── templates/         # HTML templates
│   └── static/            # Static files (CSS, JS, images)
├── migrations/            # Database migrations
├── instance/             # Instance-specific files
├── .venv/                # Virtual environment
├── main.py              # Application entry point
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
└── requirements.txt     # Python dependencies
```

## Development

### Database Migrations

To create a new migration:
```bash
flask db migrate -m "Description of changes"
```

To apply migrations:
```bash
flask db upgrade
```

### Environment Variables

Create a `.env` file in the root directory with the following variables:
```
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///instance/app.db
```

### Testing

Run the test suite:
```bash
python -m pytest
```

### Code Style

The project follows PEP 8 style guide. To check your code:
```bash
flake8 .
```

## Deployment

### Production Deployment

1. Update environment variables for production:
```
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@localhost/dbname
```

2. Build and run with Docker:
```bash
docker-compose -f docker-compose.prod.yml up --build
```

### Security Considerations

- Use HTTPS in production
- Set strong SECRET_KEY
- Regular security updates
- Database backup strategy
- Rate limiting for API endpoints

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
1. Check the documentation
2. Open an issue in the GitHub repository
3. Contact the maintainers

## Acknowledgments

- Flask community for the excellent framework
- Contributors and maintainers
- Open source community 
