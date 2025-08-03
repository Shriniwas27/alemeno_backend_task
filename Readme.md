# Credit Approval System

This project is a backend system for a credit approval process, built with Django and Django REST Framework. The system manages customer data, processes loan applications, and determines loan eligibility based on a dynamic credit scoring model. The entire application is containerized using Docker for easy setup and deployment.

## Features

  * **Customer Management**: Register new customers and manage their details.
  * **Loan Processing**: Create and view loans associated with customers.
  * **Dynamic Credit Scoring**: Calculates a credit score for customers based on their historical loan performance, including on-time payments, loan count, and current debt.
  * **Loan Eligibility Checks**: Determines if a customer is eligible for a new loan based on their credit score and current financial standing.
  * **Asynchronous Data Ingestion**: Uses Celery and Redis to ingest initial customer and loan data from Excel files without blocking the application.
  * **Dockerized Environment**: The entire application stack (web, database, cache, worker) is managed with Docker Compose for a consistent and isolated environment.

## Tech Stack

  * **Backend**: Python, Django, Django REST Framework
  * **Database**: PostgreSQL
  * **Task Queue**: Celery, Redis
  * **Containerization**: Docker, Docker Compose

## Setup and Installation

To get the application running locally, ensure you have **Docker** and **Docker Compose** installed.

**1. Clone the Repository**

```bash
git clone https://github.com/Shriniwas27/alemeno_backend_task.git
```

**2. Place Data Files**
Place the `customer_data.xlsx` and `loan_data.xlsx` files in the root of the project directory.

**3. Build and Run the Docker Containers**
This single command will build the necessary Docker images and start all the services (web server, database, etc.) in the background.

```bash
docker-compose up -d --build
```

**4. Run Database Migrations**
Apply the initial database schema migrations.

```bash
docker-compose exec web python manage.py migrate
```

**5. Ingest Initial Data**
Run the custom management command to populate the database from the provided Excel files. This is handled by a background worker.

```bash
docker-compose exec web python manage.py ingest_data
```

The application is now running and available at `http://localhost:8000`.

-----

## API Endpoints

Here are the available API endpoints for interacting with the application.

### 1\. Register a New Customer

  * **Route**: `/api/register/`
  * **Method**: `POST`
  * **Description**: Adds a new customer to the system and calculates their approved credit limit.
  * **Request Body**:
    ```json
    {
        "first_name": "John",
        "last_name": "Doe",
        "age": 30,
        "monthly_income": 50000,
        "phone_number": 1234567890
    }
    ```
  * **Success Response**: `201 Created` with the new customer's details.

### 2\. Check Loan Eligibility

  * **Route**: `/api/check-eligibility/`
  * **Method**: `POST`
  * **Description**: Checks if a customer is eligible for a loan and provides the terms.
  * **Request Body**:
    ```json
    {
        "customer_id": 1,
        "loan_amount": 100000,
        "interest_rate": 10.5,
        "tenure": 12
    }
    ```
  * **Success Response**: `200 OK` with approval status and loan terms.

### 3\. Create a New Loan

  * **Route**: `/api/create-loan/`
  * **Method**: `POST`
  * **Description**: Creates a new loan in the database if the customer is eligible.
  * **Request Body**:
    ```json
    {
        "customer_id": 1,
        "loan_amount": 50000,
        "interest_rate": 14,
        "tenure": 12
    }
    ```
  * **Success Response**: `201 Created` with the new `loan_id` if approved.

### 4\. View a Specific Loan

  * **Route**: `/api/view-loan/<loan_id>/`
  * **Method**: `GET`
  * **Description**: Retrieves details for a single loan, including nested customer information.
  * **Success Response**: `200 OK` with loan and customer details.

### 5\. View All Loans for a Customer

  * **Route**: `/api/view-loans/<customer_id>/`
  * **Method**: `GET`
  * **Description**: Retrieves a list of all loans associated with a specific customer.
  * **Success Response**: `200 OK` with a list of loan objects.
