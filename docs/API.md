# API Reference

Fieldnotes provides a REST API for authentication, posts, likes, and comments.

## Base URL

```text
http://localhost:8000
```

## API Documentation

Interactive Swagger documentation is available at:

```text
http://localhost:8000/docs
```

## Authentication

Protected endpoints require a Bearer token.

Include the following header in authenticated requests:

```http
Authorization: Bearer <token>
```

## Error Response

API errors follow this format:

```json
{
  "error": {
    "code": "forbidden",
    "message": "You can only change your own posts",
    "details": null
  }
}
```

---

# Authentication

## Register

Creates a new user account.

```http
POST /api/v1/auth/register
```

### Request Body

```json
{
  "email": "user@example.com",
  "password": "Password123!",
  "display_name": "User"
}
```

### Response

```json
{
  "access_token": "<token>",
  "token_type": "bearer",
  "user": {}
}
```

---

## Login

Signs in an existing user.

```http
POST /api/v1/auth/login
```

### Request Body

```json
{
  "email": "user@example.com",
  "password": "Password123!"
}
```

### Response

```json
{
  "access_token": "<token>",
  "token_type": "bearer",
  "user": {}
}
```

---

## Get Current User

Returns the currently signed-in user.

```http
GET /api/v1/auth/me
```

**Authentication:** Required

---

# Posts

## List Posts

Returns a paginated list of published posts.

```http
GET /api/v1/posts
```

**Authentication:** Not required

### Query Parameters

| Parameter   | Description              |
| ----------- | ------------------------ |
| `page`      | Page number              |
| `page_size` | Number of posts per page |
| `q`         | Search query             |
| `author`    | Filter by author         |
| `sort`      | Field used for sorting   |
| `order`     | Sort order               |

The list response does not include the full post body.

---

## Get Post by Slug

Returns the complete post for the specified slug.

```http
GET /api/v1/posts/by-slug/{slug}
```

**Authentication:** Not required for published posts.

Draft posts return `404` unless the signed-in user is the author.

---

## Get My Posts

Returns the signed-in user's drafts and published posts.

```http
GET /api/v1/me/posts
```

**Authentication:** Required

---

## Create Post

Creates a new draft.

```http
POST /api/v1/posts
```

**Authentication:** Required

### Request Body

```json
{
  "title": "My First Post",
  "body": "Post content goes here.",
  "excerpt": "A short description of the post."
}
```

By default, the post is created as a draft.

To publish immediately:

```http
POST /api/v1/posts?publish=true
```

---

## Update Post

Updates one of your posts.

```http
PUT /api/v1/posts/{id}
```

**Authentication:** Required

Only the post author can update the post.

---

## Publish Post

Publishes one of your posts.

```http
POST /api/v1/posts/{id}/publish
```

**Authentication:** Required

---

## Unpublish Post

Changes one of your published posts back to a draft.

```http
POST /api/v1/posts/{id}/unpublish
```

**Authentication:** Required

---

## Delete Post

Deletes one of your posts.

```http
DELETE /api/v1/posts/{id}
```

**Authentication:** Required

---

# Likes

## Toggle Like

Turns the signed-in user's like on or off for a post.

```http
POST /api/v1/posts/{id}/likes
```

**Authentication:** Required

### Response

```json
{
  "liked": true,
  "like_count": 10
}
```

Calling the endpoint again toggles the like off.

---

# Comments

## List Comments

Returns the comments for a post.

```http
GET /api/v1/posts/{id}/comments
```

---
## Add Comment

Adds a comment to a post.

```http
POST /api/v1/posts/{id}/comments
```

**Authentication:** Required

### Request Body

```json
{
  "body": "Great post!"
}
```

---

## Delete Comment

Deletes your own comment.

```http
DELETE /api/v1/comments/{id}
```

**Authentication:** Required

Only the user who created the comment can delete it.

---

# Endpoint Summary

| Method   | Endpoint                       | Auth     |
| -------- | ------------------------------ | -------- |
| `POST`   | `/api/v1/auth/register`        | No       |
| `POST`   | `/api/v1/auth/login`           | No       |
| `GET`    | `/api/v1/auth/me`              | Yes      |
| `GET`    | `/api/v1/posts`                | No       |
| `GET`    | `/api/v1/posts/by-slug/{slug}` | Optional |
| `GET`    | `/api/v1/me/posts`             | Yes      |
| `POST`   | `/api/v1/posts`                | Yes      |
| `PUT`    | `/api/v1/posts/{id}`           | Yes      |
| `POST`   | `/api/v1/posts/{id}/publish`   | Yes      |
| `POST`   | `/api/v1/posts/{id}/unpublish` | Yes      |
| `DELETE` | `/api/v1/posts/{id}`           | Yes      |
| `GET`    | `/api/v1/posts/{id}/comments`  | No       |
| `POST`   | `/api/v1/posts/{id}/comments`  | Yes      |
| `DELETE` | `/api/v1/comments/{id}`        | Yes      |
| `POST`   | `/api/v1/posts/{id}/likes`     | Yes      |
