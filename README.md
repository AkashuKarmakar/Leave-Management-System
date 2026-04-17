# Leave Management System API

A lightweight RESTful API for managing HR leave requests, built with Python 3.10+ and FastAPI.

## Features

- **Thread Safety**: Implements file-level locking using `portalocker`.
- **Flat-file DB**: Uses `database.json` for persistence.
- **Auto-increment**: Automatically manages IDs for employees and leaves.
- **Interactive Docs**: Swagger UI available at `/docs`.

## Local Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
