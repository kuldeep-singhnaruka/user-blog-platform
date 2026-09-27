import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

export default function Editor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [excerpt, setExcerpt] = useState("");
  const [body, setBody] = useState("");
  const [status, setStatus] = useState("draft");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    api(`/api/v1/posts/${id}`)
      .then((post) => {
        setTitle(post.title);
        setExcerpt(post.excerpt);
        setBody(post.body);
        setStatus(post.status);
      })
      .catch((err) => setError(err.message));
  }, [id]);

  function payload() {
    return { title, body, excerpt: excerpt || null };
  }

  async function save(publish) {
    setError("");
    try {
      let post;
      if (!id) {
        post = await api(`/api/v1/posts?publish=${publish ? "true" : "false"}`, { method: "POST", body: payload() });
      } else {
        post = await api(`/api/v1/posts/${id}`, { method: "PUT", body: payload() });
        if (publish && post.status !== "published") post = await api(`/api/v1/posts/${id}/publish`, { method: "POST" });
        if (!publish && status === "published") post = await api(`/api/v1/posts/${id}/unpublish`, { method: "POST" });
      }
      navigate(post.status === "published" ? `/posts/${post.slug}` : "/me");
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove() {
    if (!id || !window.confirm("Delete this note?")) return;
    await api(`/api/v1/posts/${id}`, { method: "DELETE" });
    navigate("/me");
  }

  return (
    <section className="editor">
      <p className="eyebrow">{id ? `Editing · ${status}` : "New note"}</p>
      <h1>{id ? "Revise" : "Write"}</h1>
      <label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} required minLength={3} /></label>
      <label>Excerpt<input value={excerpt} onChange={(event) => setExcerpt(event.target.value)} placeholder="Optional" /></label>
      <label>Body<textarea value={body} onChange={(event) => setBody(event.target.value)} rows={14} required /></label>
      {error && <p className="error">{error}</p>}
      <div className="actions">
        <button type="button" className="button ghost" onClick={() => save(false)}>Save draft</button>
        <button type="button" className="button" onClick={() => save(true)}>Publish</button>
        {id && <button type="button" className="text-button danger" onClick={remove}>Delete</button>}
      </div>
    </section>
  );
}
