# Usage
This guide covers the main user flows in Fieldnotes.

## Start the Application

### 1. Start the API
Open a terminal and start the backend from the `backend` folder on port `8000`.

### 2. Start the Website
Open a second terminal and start the frontend from the `frontend` folder.

### 3. Open the Website
Open:

```text
http://localhost:5173
```

---

# Read Posts

You can read published posts without signing in.

1. Stay signed out.
2. Open the home page.
3. Select a published post.
4. Read the full post.

Mina's draft is not displayed on the public home page.

---

# Write a Post

Sign in using the author account:

```text
Email:    mina@fieldnotes.local
Password: Author123!
```

### My Desk
Open **My Desk** to see Mina's posts.
The list includes the draft:

```text
Notes from the desk
```

Open the draft and select **Publish**.
Once published, the post becomes visible on the public home page.

### Post Actions

| Action         | Result                          |
| -------------- | ------------------------------- |
| **Write**      | Starts a new post               |
| **Save Draft** | Keeps the post private          |
| **Publish**    | Makes the post publicly visible |
| **Delete**     | Removes the post                |

---

# Like and Comment
Sign out from the author account and sign in as the reader:

```text
Email:    ravi@fieldnotes.local
Password: Reader123!
```

1. Open one of Mina's published posts.
2. Click **Like**.
3. Add a comment.
4. Confirm that the post does not show an **Edit** button.

Ravi can interact with Mina's published post, but cannot edit or manage it.

---

# Reset the Application
To reset the local database and recreate the demo data:

1. Stop the API server.
2. Delete the database file:

```text
backend/data/blog.db
```

3. Start the API again.
The application will create the database and demo posts again on startup.
