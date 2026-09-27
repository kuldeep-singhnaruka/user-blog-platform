# Architecture

Fieldnotes uses a simple frontend and backend architecture. The website and API run as separate applications and communicate through HTTP requests using JSON.

## Application Architecture

```text
Browser
http://localhost:5173
      |
      | JSON / HTTP
      v
FastAPI
http://localhost:8000
      |
      +-- Routes
      |     Handles HTTP requests
      |
      +-- Services
      |     Applies business rules
      |
      +-- Models
      |     Users, blogs, posts, comments, likes
      |
      v
SQLite
backend/data/blog.db
```

## Components

### Frontend
The frontend runs on:

```text
http://localhost:5173
```

It provides the user interface and communicates with the backend API using HTTP requests.

### Backend
The backend is built with FastAPI and runs on:

```text
http://localhost:8000
```

The backend is responsible for handling requests, applying business rules, authentication, and database operations.

### Routes
Routes receive HTTP requests and return API responses.

They are responsible for:

* Validating incoming requests
* Handling authentication
* Calling the appropriate service
* Returning the API response

### Services

Services contain the application's business rules.

They determine whether an operation is allowed before making changes to the database.

### Models

Models represent the main database entities:

* Users
* Blogs
* Posts
* Comments
* Likes

### Database

Fieldnotes uses SQLite for local development.

Database file:

```text
backend/data/blog.db
```

---

# Application Rules

The following rules are enforced by the backend.

### Published Posts
Published posts can be read without an account.

### Draft Posts
Draft posts are visible only to their author.

### User Blogs
When a user registers, a blog is created for that user.

New posts created by the user are associated with their blog.

### Post Ownership
Only the post author can:

* Edit a post
* Publish a post
* Unpublish a post
* Delete a post

### Likes and Comments
Any authenticated user can:

* Like a published post
* Remove their like
* Add a comment to a published post

### Comment Ownership
A user can delete only comments that they created.

---

# Authentication
Fieldnotes uses token-based authentication.

## Password Storage
Passwords are never stored as plain text.

When a user registers, the password is converted into a secure hash before being stored in the database.

```text
Password
   |
   v
Password Hash
   |
   v
Database
```

## Login Flow
After a successful login, the API returns an authentication token.

```text
User
  |
  | Email + Password
  v
FastAPI
  |
  | Verify password
  v
Authentication Token
  |
  v
Browser
```

The browser sends the token with subsequent authenticated requests:

```http
Authorization: Bearer <token>
```

The backend uses the token to identify the user.

Authentication answers:

> Who is this user?

Authorization answers:

> What is this user allowed to change?

For example, a valid token identifies the current user, while the post ownership check determines whether that user is allowed to edit a specific post.
