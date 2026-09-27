"""Demo users and posts so the reading room is not empty on first launch."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import Blog, Comment, Like, Post, User
from app.models.types import utcnow
from app.services.slugs import slugify


DEMO_NOTES = [
    {
        "title": "A boundary is a feature",
        "excerpt": "The useful part of a service is the line it refuses to cross. Fieldnotes keeps reading public and writing private to the author.",
        "published": True,
        "days_ago": 6,
        "body": """A production system gets easier to change when each layer has one job. The boundary is not extra paperwork. It is the feature that tells the next person where a change is allowed to stop.

## What each layer owns

Routes accept the HTTP request and check that the payload has the expected shape. Services decide what is allowed. Repositories run the queries. Models describe the tables: users, blogs, posts, comments, and likes.

If a permission check leaks into the route and again into the query, the same rule gets two answers. Fieldnotes keeps the decision in the service. The route only carries the request across.

## Who can see a note

Anyone can open a published note. No account is required for the reading room. A draft is a different object: it stays on the author's desk and returns 404 to everyone else, including other signed-in users.

That split is the product. Publishing is the moment a private note becomes a public one. Unpublishing sends it back.

## What you can change

Only the author can edit, publish, unpublish, or delete a post. Another account can like a published note or leave a comment. Liking does not grant edit access. A comment can be deleted only by the person who wrote it.

The token answers who is calling. The author check answers what they may touch.""",
    },
    {
        "title": "Authentication is not authorization",
        "excerpt": "Signing in proves who you are. It does not decide what you may touch. Those are two different questions.",
        "published": True,
        "days_ago": 3,
        "body": """A login form feels like a door. Once you are inside, it is tempting to treat every button as yours. Fieldnotes does not work that way. Signing in and being allowed to change a note are separate checks.

## The token

The password is stored as a hash, never as the original text. After a successful login the API returns a token. The browser sends that token on later requests. The token says which account is calling. It expires. It is not a permission list.

Register does one more thing: it creates a blog for that user. New posts are saved on that blog, under that author.

## The author check

After the token is accepted, the service looks at the post. If you are the author, you can edit the title and body, publish it, hide it again, or delete it. If you are not the author, those routes return 403. The note stays as the writer left it.

Ravi can read Mina's published work, like it, and comment. Ravi does not see an Edit button on Mina's post, and the API would refuse the edit even if the button were forced.

## A new account starts empty

Your own login does not inherit Mina's notes. The home page shows published notes from every author. My desk shows only the notes on your blog, including drafts, plus how many people liked each one. Until you write something, that desk is empty on purpose.""",
    },
    {
        "title": "What a like actually counts",
        "excerpt": "A like is one person choosing a published note. The count on the desk is that number, not a score the author can edit.",
        "published": True,
        "days_ago": 1,
        "body": """The number next to a note is a count of rows, not a mood. Each like is one user attached to one published post. The same person cannot be counted twice: liking again removes the like.

## Where the number shows up

On the home page every card shows likes and comments beside the author and the date. Open the note and the same numbers sit in the detail strip, with the reading time and the blog name. On My desk the author sees a total across their notes and a count on each row.

A draft can show zero likes because it is not in the public room yet. People cannot like what they cannot open.

## What the count does not do

A like does not transfer ownership. It does not unlock edit, publish, or delete. Comments are the same kind of boundary: anyone signed in can leave one on a published note, and only that comment's author can remove it.

If you want the number to change, sign in as a different reader and press Like. The author's desk updates because it reads the same table, not because the author typed the number in.""",
    },
    {
        "title": "Notes from the desk",
        "excerpt": "A draft stays with the author until it is published. This one is still private.",
        "published": False,
        "days_ago": 0,
        "body": """This draft is on Mina's desk and hidden from the public feed.

## Still private

The home page lists published notes only. Searching the shelf will not find this title. Opening it by its address returns not found unless the viewer is Mina.

## Ready when she says so

Publish moves it into the reading room and stamps a published date. Until then it counts on her desk as a note she posted, and as a draft rather than a published blog. Save draft keeps further edits private. Delete removes it for good.""",
    },
]


OTHER_AUTHORS = [
    {
        "email": "anika@fieldnotes.local",
        "password": "Author123!",
        "display_name": "Anika Sen",
        "note": {
            "title": "A comment belongs to its writer",
            "excerpt": "Leaving a comment does not make the note yours. You can remove the words you wrote, and nothing else on that page.",
            "published": True,
            "days_ago": 2,
            "body": """A published note is a shared room with one owner. Readers can speak in it. They cannot rearrange the furniture.

## What a reader may add

Any signed-in person can leave a comment on a published note. The comment stores their account, the time, and the text. The home page counts those comments on the card. The note itself still belongs to the author.

## What they may remove

Delete is limited to the comment you wrote. Anika can remove her own reply. She cannot remove Ravi's reply, and she cannot delete Mina's note. The API returns forbidden if she tries.

That is the same idea as the desk. Your name is on your words. Someone else's name stays on theirs.""",
        },
    },
    {
        "email": "farhan@fieldnotes.local",
        "password": "Author123!",
        "display_name": "Farhan Qureshi",
        "note": {
            "title": "Publish is the moment it leaves the desk",
            "excerpt": "A draft is a private page. Publish is the switch that puts the title on the shelf, with your name and the date beside it.",
            "published": True,
            "days_ago": 4,
            "body": """Writing and showing are different steps. The desk can hold a note for as long as the author wants. The shelf only lists notes that have been published.

## Before publish

The draft has a title, an excerpt, and a body. It counts on the author's desk. It does not appear in search, and another account cannot open it. Likes stay at zero because there is no public page to like.

## After publish

The note gets a published date. The card on the home page shows the author's name, that date, the excerpt, and the like and comment counts. Unpublish sends it back to the desk and off the shelf. The words are still the author's. The room they sit in is what changed.""",
        },
    },
]


def seed_database(db: Session) -> None:
    if not settings.seed_demo_data:
        return
    if db.scalar(select(User.id).limit(1)):
        _enrich_short_demo_notes(db)
        _ensure_other_authors(db)
        return

    mina, mina_blog = _account(db, "mina@fieldnotes.local", "Author123!", "Mina Rao")
    ravi, _ravi_blog = _account(db, "ravi@fieldnotes.local", "Reader123!", "Ravi Shah")
    first = None
    for note in DEMO_NOTES:
        post = _post(db, mina, mina_blog, note)
        if first is None and note["published"]:
            first = post
    db.add(Comment(post_id=first.id, author_id=ravi.id, body="The public reading room is the part I want to remember."))
    db.add(Like(post_id=first.id, user_id=ravi.id))
    _ensure_other_authors(db)
    db.flush()


def _ensure_other_authors(db: Session) -> None:
    for spec in OTHER_AUTHORS:
        user = db.scalar(select(User).where(User.email == spec["email"]))
        if user is None:
            user, blog = _account(db, spec["email"], spec["password"], spec["display_name"])
        else:
            blog = db.scalar(select(Blog).where(Blog.owner_id == user.id))
        slug = slugify(spec["note"]["title"])
        existing = db.scalar(select(Post).where(Post.slug == slug))
        if existing is None:
            _post(db, user, blog, spec["note"])
    db.flush()


def _enrich_short_demo_notes(db: Session) -> None:
    mina = db.scalar(select(User).where(User.email == "mina@fieldnotes.local"))
    if mina is None:
        return
    blog = db.scalar(select(Blog).where(Blog.owner_id == mina.id))
    if blog is None:
        return
    for note in DEMO_NOTES:
        slug = slugify(note["title"])
        post = db.scalar(select(Post).where(Post.slug == slug, Post.author_id == mina.id))
        if post is None:
            _post(db, mina, blog, note)
            continue
        if len(post.body) >= 500:
            continue
        post.excerpt = note["excerpt"]
        post.body = note["body"].strip()
        post.updated_at = utcnow()
    db.flush()


def _account(db: Session, email: str, password: str, display_name: str) -> tuple[User, Blog]:
    user = User(email=email.lower(), password_hash=hash_password(password), display_name=display_name)
    db.add(user)
    db.flush()
    base = slugify(display_name)
    slug = base
    suffix = 2
    while db.scalar(select(Blog.id).where(Blog.slug == slug)):
        slug = f"{base}-{suffix}"
        suffix += 1
    blog = Blog(owner_id=user.id, name=f"{display_name}'s notes", slug=slug)
    db.add(blog)
    db.flush()
    return user, blog


def _post(db: Session, author: User, blog: Blog, note: dict) -> Post:
    published = note["published"]
    when = utcnow() - timedelta(days=note["days_ago"])
    post = Post(
        blog_id=blog.id,
        author_id=author.id,
        title=note["title"],
        slug=slugify(note["title"]),
        excerpt=note["excerpt"],
        body=note["body"].strip(),
        status="published" if published else "draft",
        published_at=when if published else None,
        created_at=when,
        updated_at=when,
    )
    db.add(post)
    db.flush()
    return post
