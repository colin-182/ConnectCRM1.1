# ConnectCRM1.1
ConnectCRM

ConnectCRM is a multi-tenant customer relationship management (CRM) web
application built with Django. It allows businesses to manage companies,
contacts, deals, tasks, team memberships and invitations from a central
dashboard.

Repository

GitHub: https://github.com/colin-182/ConnectCRM1.1

Render: https://connectcrm1-1.onrender.com

Features

User registration, login, logout and password reset

Business/workspace-based multi-tenancy

Companies CRUD and company search

Google Places business search during company creation

Contacts CRUD with company relationships

Deals CRUD with company/contact relationships

Deal stages and pipeline values

Tasks CRUD with due dates and times

Task completion/reopening

Live dashboard KPIs and pipeline information

Team-member pipeline information for administrators

Business invitations and membership roles

Search across CRM records

Business-level data isolation

Production PostgreSQL support

Static file handling with WhiteNoise

Technology Stack

Python

Django 6.1

PostgreSQL

Neon PostgreSQL

Gunicorn

WhiteNoise

dj-database-url

psycopg

Google Places API

HTML/CSS/JavaScript

Render

Project Structure

ConnectCRM1.1/
├── accounts/
│   ├── tests/
│   └── ...
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── tests/
│   └── ...
├── crm/
│   ├── services/
│   │   └── google_places.py
│   ├── tests/
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── templates/
├── static/
├── manage.py
├── requirements.txt
└── README.md

Local Development

1. Clone the repository

git clone https://github.com/colin-182/ConnectCRM1.1.git
cd ConnectCRM1.1

2. Create and activate a virtual environment

macOS/Linux:

python3 -m venv venv
source venv/bin/activate

Windows:

python -m venv venv
venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Configure environment variables

Configure the required environment variables locally. Typical settings
include:

SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DATABASE_URL=your-postgresql-database-url
GOOGLE_PLACES_API_KEY=your-google-places-api-key

Never commit secrets, API keys or production database credentials to
Git.

5. Run migrations

python manage.py migrate

6. Run checks

python manage.py check

For production checks:

python manage.py check --deploy

7. Run tests

python manage.py test

8. Start the development server

python manage.py runserver

The application will normally be available at http://127.0.0.1:8000/.

Production Deployment

ConnectCRM is configured for deployment on Render.

Build command

pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate

Start command

gunicorn config.wsgi:application

Production environment

At minimum, configure the required application secrets and connection
details on Render, including:

SECRET_KEY=<production-secret>
DJANGO_DEBUG=False
DATABASE_URL=<postgresql-connection-string>
GOOGLE_PLACES_API_KEY=<google-api-key>

The application uses DATABASE_URL to connect to PostgreSQL in
production.

Static Files

WhiteNoise is used to serve static files in production.

Render collects static files during the build:

python manage.py collectstatic --noinput

Database

Production uses PostgreSQL. The database connection is supplied through
DATABASE_URL, allowing the application to use a hosted PostgreSQL
provider such as Neon.

Apply migrations with:

python manage.py migrate

Testing

The project includes tests covering areas including:

Authentication

User profiles

Dashboard behaviour

CRM CRUD functionality

Deal ownership

Search

Security

Multi-tenant data isolation

UI behaviour

Invitation permissions

Run the full test suite with:

python manage.py test

Additional useful checks:

python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run

Multi-Tenancy and Security

Business isolation is a core part of ConnectCRM.

CRM records are associated with a business/workspace, and views scope
database queries to the current business. This prevents users from
accessing another business's CRM records through URLs or record IDs.

The application also keeps the Google API credential server-side.

For production:

Set DJANGO_DEBUG=False

Use a secure SECRET_KEY

Store database credentials in environment variables

Store Google API credentials in environment variables

Do not commit .env files or credentials to source control

Google Places Integration

The company creation workflow can search for businesses using Google
Places.

The browser calls an authenticated Django endpoint. The server performs
the Google Places search and returns the results to the application,
keeping the API key server-side.

Main CRM Routes

Examples of the main CRM routes are:

/crm/companies/
/crm/companies/add/
/crm/contacts/
/crm/contacts/add/
/crm/deals/
/crm/deals/add/
/crm/tasks/
/crm/tasks/add/
/crm/search/

Development Checklist

Before committing changes:

python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test

Before a production release:

python manage.py check --deploy

Then verify the Render deployment and test the live application
end-to-end.

Deployment Checklist

Django checks pass

Migration check passes

Full test suite passes

gunicorn is included in requirements.txt

psycopg[binary] is included in requirements.txt

dj-database-url is included in requirements.txt

DJANGO_DEBUG=False is configured on Render

Production SECRET_KEY is configured

DATABASE_URL points to the production PostgreSQL database

Google Places API key is configured

Static files collect successfully

Database migrations complete successfully

Render deployment completes successfully

Registration and login work

Company, contact, deal and task workflows work

Google business search works

Dashboard data updates correctly

Business data isolation has been verified



