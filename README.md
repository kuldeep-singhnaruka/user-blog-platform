# Fieldnotes

A small blog application built for the Week 1 Bootcamp.

Fieldnotes allows users to read, create, manage, like, and comment on blog posts based on their account permissions.

## Features

* Read published blog posts without signing in
* Sign in to create and manage your own posts
* Save posts as drafts
* Publish your posts
* Like published posts
* Comment on published posts
* User-based access control
* Separate frontend and backend applications

## Tech Stack

### Frontend

* JavaScript
* Node.js
* npm

### Backend

* Python
* FastAPI
* Uvicorn

### Architecture

The application follows a simple layered architecture:

```text
Browser
   │
   ▼
Frontend
   │
   ▼
Python API
   │
   ├── API Routes
   ├── Services
   ├── Repositories
   └── Models
        │
        ▼
     Database
```

## Project Structure

```text
fieldnotes/
│
├── frontend/
│   └── Website and frontend application
│
├── backend/
│   └── Python API
│       └── app/
│           ├── api/
│           │   └── routes/
│           ├── services/
│           ├── models/
│           └── repositories/
│
├── docs/
│   └── Additional project documentation
│
└── README.md
```

### Backend Layers

| Directory       | Responsibility                          |
| --------------- | --------------------------------------- |
| `api/routes/`   | Handles HTTP requests and responses     |
| `services/`     | Contains application and business logic |
| `models/`       | Defines database models                 |
| `repositories/` | Handles database queries                |

## Run Locally

### 1. Start the Backend

Open a terminal and run:

```bash
cd backend
../.venv/bin/uvicorn app.main:app --reload --port 8000
```

The backend will be available at:

```text
http://localhost:8000
```

### 2. Start the Frontend

Open a second terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

Open the application in your browser:

**http://localhost:5173**

## Demo Accounts

The first application launch creates two demo accounts.

| Email                   | Password     | Role   |
| ----------------------- | ------------ | ------ |
| `mina@fieldnotes.local` | `Author123!` | Author |
| `ravi@fieldnotes.local` | `Reader123!` | Reader |

### Author Account

The author account has:

* Published posts
* One draft post
* Permission to create posts
* Permission to manage its own posts

### Reader Account

The reader account can:

* Read published posts
* Like posts
* Comment on posts

## How It Works

The browser communicates with the Python API.

```
User
 │
 ▼
Frontend
 │
 │ HTTP requests
 ▼
API Routes
 │
 ▼
Services
 │
 ▼
Repositories
 │
 ▼
Database
```

Each layer has a specific responsibility, which keeps the application organized and easier to maintain.

## Documentation

Additional documentation is available in:

```text
docs/
```

Refer to the documentation for more detailed information about the application and its implementation.
