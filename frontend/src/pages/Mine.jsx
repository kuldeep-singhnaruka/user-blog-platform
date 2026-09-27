import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";

function people(count) {
  return count === 1 ? "1 person" : `${count} people`;
}

export default function Mine() {
  const { user } = useAuth();
  const [page, setPage] = useState(null);
  const [error, setError] = useState("");
  const posts = page?.data ?? null;

  function load() {
    api("/api/v1/me/posts?page_size=50")
      .then(setPage)
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function remove(id) {
    if (!window.confirm("Delete this note?")) return;
    await api(`/api/v1/posts/${id}`, { method: "DELETE" });
    load();
  }

  const posted = page?.meta.total ?? 0;
  const published = posts?.filter((post) => post.status === "published").length ?? 0;
  const likes = posts?.reduce((sum, post) => sum + post.like_count, 0) ?? 0;

  return (
    <section>
      <p className="eyebrow">Your blog</p>
      <h1>{user.display_name}'s desk</h1>
      <p className="muted">Drafts stay here. Published notes appear in the reading room. Each note shows how many people liked it.</p>
      {posts && (
        <div className="stats">
          <article className="stat">
            <strong>{posted}</strong>
            <span>{posted === 1 ? "blog posted" : "blogs posted"}</span>
          </article>
          <article className="stat">
            <strong>{published}</strong>
            <span>{published === 1 ? "published blog" : "published blogs"}</span>
          </article>
          <article className="stat">
            <strong>{likes}</strong>
            <span>{likes === 1 ? "person liked your blogs" : "people liked your blogs"}</span>
          </article>
        </div>
      )}
      <div className="actions">
        <Link className="button" to="/write">New note</Link>
      </div>
      {error && <p className="error">{error}</p>}
      <table className="desk">
        <thead>
          <tr><th>Title</th><th>Status</th><th>Likes</th><th></th></tr>
        </thead>
        <tbody>
          {posts?.map((post) => (
            <tr key={post.id}>
              <td>{post.status === "published" ? <Link to={`/posts/${post.slug}`}>{post.title}</Link> : post.title}</td>
              <td><span className={post.status === "published" ? "pill live" : "pill"}>{post.status}</span></td>
              <td>{people(post.like_count)}</td>
              <td className="row-actions">
                <Link to={`/edit/${post.id}`}>Edit</Link>
                <button type="button" className="text-button" onClick={() => remove(post.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {posts && posts.length === 0 && <p className="empty">Your desk is empty. Write the first note.</p>}
    </section>
  );
}
