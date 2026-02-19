# FastAPI Backend Learning Project

This repository is a personal learning project for exploring Python, FastAPI, and SQLAlchemy. It provides a simple backend API for a React frontend, but the main goal is to experiment and learn Python web development concepts.

## About This Project

- This codebase is for learning purposes and may contain errors, incomplete features, or non-optimal code.
- The API and database are not guaranteed to be fully functional at all times.

## Features

- FastAPI for building APIs
- SQLite database (auto-created)
- SQLAlchemy ORM
- Basic CRUD endpoints for items

## Endpoints

- `POST /items/` - Create a new item
- `GET /items/` - List all items
- `GET /items/{item_id}` - Get a single item
- `DELETE /items/{item_id}` - Delete an item

## Setup

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Run the server (from your virtual environment):
   ```sh
   uvicorn main:app --reload
   ```

The API will be available at http://127.0.0.1:8000

## Notes

- The database file `app.db` is created automatically in the project directory.
- You can test the API using the interactive docs at http://127.0.0.1:8000/docs
- This project is a work in progress and intended for experimentation and learning.
