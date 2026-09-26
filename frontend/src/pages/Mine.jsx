import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, downloadExport } from "../api";
import { useAuth } from "../auth";

export default function Mine() {
  const { user } = useAuth();
  const [posts, setPosts] = useState(null);
  const [blog, setBlog] = useState(null);
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  function load() {
    api("/api/v1/me/posts?page_size=50")
      .then((page) => setPosts(page.data))
      .catch((err) => setError(err.message));
    api("/api/v1/auth/me/blog")
      .then((next) => {
        setBlog(next);
        setDescription(next.description || "");
      })
      .catch(() => {});
  }

  useEffect(load, []);

  async function saveBlog(event) {
    event.preventDefault();
    const next = await api("/api/v1/auth/me/blog", {
      method: "PATCH",
      body: { description },
    });
    setBlog(next);
  }

  async function remove(id) {
    if (!window.confirm("Delete this note?")) return;
    await api(`/api/v1/posts/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <section>
      <p className="eyebrow">Your tenant</p>
      <h1>{blog?.name || `${user.display_name}'s desk`}</h1>
      <p className="muted">Drafts stay here. Published notes appear in the reading room.</p>
      {blog && (
        <form className="inline-form" onSubmit={saveBlog}>
          <input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Blog description" />
          <button className="button ghost" type="submit">
            Save
          </button>
        </form>
      )}
      <div className="actions">
        <Link className="button" to="/write">
          New note
        </Link>
        <button type="button" className="button ghost" onClick={() => downloadExport("csv")}>
          Export CSV
        </button>
        <button type="button" className="button ghost" onClick={() => downloadExport("xlsx")}>
          Export Excel
        </button>
        <button type="button" className="button ghost" onClick={() => downloadExport("pdf")}>
          Export PDF
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      <table className="desk">
        <thead>
          <tr>
            <th>Title</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {posts?.map((post) => (
            <tr key={post.id}>
              <td>
                {post.status === "published" ? <Link to={`/posts/${post.slug}`}>{post.title}</Link> : post.title}
              </td>
              <td>
                <span className={post.status === "published" ? "pill live" : "pill"}>{post.status}</span>
              </td>
              <td className="row-actions">
                <Link to={`/edit/${post.id}`}>Edit</Link>
                <button type="button" className="text-button" onClick={() => remove(post.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {posts && posts.length === 0 && <p className="empty">Your desk is empty. Write the first note.</p>}
    </section>
  );
}
