Leave Management System (Python API)
A lightweight, high-performance RESTful API for managing employee leave requests, balances, and records. Built with Python 3.14 (Flask) to ensure rapid iteration and clear documentation.
🚀 Live Demo
Interactive Swagger UI (live link ): https://leave-management-system-2-j5ax.onrender.com/apidocs/
🛠 Features
Employee Management: Create, update, and retrieve employee details.
Leave Request Management: Automated calculation of leave days based on date ranges.
Leave Balance Tracking: Track yearly quotas (Annual, Sick, Casual) per employee.
Validation Engine: Real-time endpoint to check balance availability before submission.
Data Persistence: Uses a thread-safe flat-file database.json store with file-level locking.
Interactive Documentation: Built-in Swagger UI for easy API testing.
💻 Local Setup & Run Instructions

1. Prerequisites
   Python 3.10+ (Tested on Python 3.14)
   Pip (Python package manager)
2. Installation
   Clone the repository and navigate to the project folder:
   code
   Bash
   git clone https://github.com/AkashuKarmakar/Leave-Management-System.git
   Create and activate a virtual environment (optional but recommended):
   code
   Bash
   python -m venv env

   # On Windows:

   .\env\Scripts\activate

   # On Mac/Linux:

   source env/bin/activate
   Install the necessary packages:
   code
   Bash
   pip install -r requirements.txt

3. Running the API
   Start the local development server:
   code
   Bash
   python app.py
   The API will be available at: http://127.0.0.1:8000
   📖 API Documentation
   Once the server is running, you can access the following:
   Interactive Swagger UI: http://127.0.0.1:8000/apidocs/
   Raw OpenAPI JSON Spec: http://127.0.0.1:8000/openapi.json
   Core Endpoints
   Method Endpoint Description
   GET /api/employees Fetch all or specific employee
   POST /api/employees Create or update employee records
   POST /api/leaves Submit a leave request (Auto-deducts balance)
   GET /api/leaves/employee/{id} Retrieve leave history for an employee
   GET /api/leavebalances/employee/{id}/year/{year} Check available quotas
   GET /api/validate-leave Validate if a leave period is available
   ☁️ Deployment Instructions (Render)
   This project is configured for deployment on Render.com.
   GitHub: Push your code to a public GitHub repository.
   New Web Service: Create a new Web Service on Render and connect your repository.
   Environment: Select Python 3.
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   Live URL: Render will provide a public URL once the build is complete.
   📂 Project Structure
   app.py: The core Flask application logic and API routes.
   database.json: The flat-file document store (Pre-populated with sample data).
   requirements.txt: Python dependencies (Flask, Flasgger, Portalocker, Gunicorn).
   README.md: Setup and deployment guide.
   📝 Technical Notes
   Thread Safety: The system uses the portalocker library to ensure that multiple API calls do not corrupt the database.json file during simultaneous write operations.
   Auto-Increment: IDs for employees and leave requests are managed automatically via metadata tracking in the JSON store.
