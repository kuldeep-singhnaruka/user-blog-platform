import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { coverFor, coverStyle } from "../covers";
import { formatWhen, people, posterTone, readingMinutes } from "../format";
import { renderMarkdown } from "../markdown";

export default function PostPage() {
  const { slug } = useParams();
  const { user } = useAuth();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [body, setBody] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    api(`/api/v1/posts/by-slug/${slug}`)
      .then(async (next) => {
        setPost(next);
        setComments(await api(`/api/v1/posts/${next.id}/comments`));
      })
      .catch((err) => setError(err.message));
  }, [slug, user?.id]);

  async function toggleLike() {
    const result = await api(`/api/v1/posts/${post.id}/likes`, { method: "POST" });
    setPost({ ...post, liked_by_me: result.liked, like_count: result.like_count });
  }

  async function addComment(event) {
    event.preventDefault();
    const created = await api(`/api/v1/posts/${post.id}/comments`, { method: "POST", body: { body } });
    setComments([...comments, created]);
    setBody("");
    setPost({ ...post, comment_count: post.comment_count + 1 });
  }

  async function removeComment(id) {
    await api(`/api/v1/comments/${id}`, { method: "DELETE" });
    setComments(comments.filter((item) => item.id !== id));
  }

  if (error) return <p className="error page-note">{error}</p>;
  if (!post) return <p className="muted page-note">Opening the note…</p>;

  const minutes = readingMinutes(post.body);
  const tone = posterTone(post.id);
  const cover = coverFor(post.slug);

  return (
    <article className="reading">
      <header className={cover ? "note-banner has-cover" : "note-banner"} style={coverStyle(post.slug, tone)}>
        <p className="poster-kicker">{post.status === "published" ? "Published note" : "Draft"}</p>
        <h1>{post.title}</h1>
        <p className="lede">{post.excerpt}</p>
        <p className="byline">
          <Link to={`/?author=${post.blog_slug}`}>{post.author_display_name}</Link>
          <span>{formatWhen(post.published_at)}</span>
          <span>{minutes} min read</span>
          <span>{people(post.like_count, "like")}</span>
          <span>{people(post.comment_count, "comment")}</span>
        </p>
      </header>
      <div className="prose" dangerouslySetInnerHTML={{ __html: renderMarkdown(post.body) }} />
      <div className="actions">
        {user ? (
          <button type="button" className={post.liked_by_me ? "button" : "button ghost"} onClick={toggleLike}>
            {post.liked_by_me ? "Liked" : "Like"} · {post.like_count}
          </button>
        ) : (
          <Link to="/login" className="button ghost">Sign in to like · {post.like_count}</Link>
        )}
        {post.can_edit && <Link to={`/edit/${post.id}`} className="button ghost">Edit</Link>}
      </div>
      <section className="comments">
        <h2>Comments</h2>
        {comments.length === 0 && <p className="muted">No comments yet.</p>}
        <ul>
          {comments.map((comment) => (
            <li key={comment.id}>
              <strong>{comment.author_display_name}</strong>
              <span>{formatWhen(comment.created_at)}</span>
              <p>{comment.body}</p>
              {comment.can_delete && (
                <button type="button" className="text-button" onClick={() => removeComment(comment.id)}>Delete</button>
              )}
            </li>
          ))}
        </ul>
        {user ? (
          <form onSubmit={addComment}>
            <textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="Leave a comment" required maxLength={2000} />
            <button className="button" type="submit">Comment</button>
          </form>
        ) : (
          <p><Link to="/login">Sign in</Link> to comment.</p>
        )}
      </section>
    </article>
  );
}
