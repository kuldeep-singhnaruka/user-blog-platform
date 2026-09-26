import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { renderMarkdown } from "../markdown";

export default function PostPage() {
  const { slug } = useParams();
  const { user } = useAuth();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [body, setBody] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const next = await api(`/api/v1/posts/by-slug/${slug}`);
    setPost(next);
    const thread = await api(`/api/v1/posts/${next.id}/comments`);
    setComments(thread);
  }

  useEffect(() => {
    setError("");
    load().catch((err) => setError(err.message));
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
    setPost({ ...post, comment_count: Math.max(0, post.comment_count - 1) });
  }

  if (error) return <p className="error page-note">{error}</p>;
  if (!post) return <p className="muted page-note">Opening the note…</p>;

  return (
    <article className="reading">
      <p className="eyebrow">{post.tags.join(" · ") || "note"}</p>
      <h1>{post.title}</h1>
      <p className="byline">
        {post.author_display_name}
        <Link to={`/?author=${post.blog_slug}`}>{post.blog_name}</Link>
      </p>
      {post.cover_url && <img className="hero-image" src={post.cover_url} alt="" />}
      <div className="prose" dangerouslySetInnerHTML={{ __html: renderMarkdown(post.body) }} />
      {post.reference_extract && (
        <aside className="reference">
          <p className="eyebrow">From the public web</p>
          <h2>{post.reference_title}</h2>
          <p>{post.reference_extract}</p>
          {post.reference_url && (
            <a href={post.reference_url} target="_blank" rel="noreferrer">
              Open source
            </a>
          )}
        </aside>
      )}
      <div className="actions">
        {user ? (
          <button type="button" className={post.liked_by_me ? "button" : "button ghost"} onClick={toggleLike}>
            {post.liked_by_me ? "Liked" : "Like"} · {post.like_count}
          </button>
        ) : (
          <Link to="/login" className="button ghost">
            Sign in to like · {post.like_count}
          </Link>
        )}
        {post.can_edit && (
          <Link to={`/edit/${post.id}`} className="button ghost">
            Edit
          </Link>
        )}
      </div>

      <section className="comments">
        <h2>Comments</h2>
        {comments.length === 0 && <p className="muted">No comments yet.</p>}
        <ul>
          {comments.map((comment) => (
            <li key={comment.id}>
              <strong>{comment.author_display_name}</strong>
              <p>{comment.body}</p>
              {comment.can_delete && (
                <button type="button" className="text-button" onClick={() => removeComment(comment.id)}>
                  Delete
                </button>
              )}
            </li>
          ))}
        </ul>
        {user ? (
          <form onSubmit={addComment}>
            <textarea
              value={body}
              onChange={(event) => setBody(event.target.value)}
              placeholder="Leave a comment"
              required
              maxLength={2000}
            />
            <button className="button" type="submit">
              Comment
            </button>
          </form>
        ) : (
          <p>
            <Link to="/login">Sign in</Link> to comment.
          </p>
        )}
      </section>
    </article>
  );
}
