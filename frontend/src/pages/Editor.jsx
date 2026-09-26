import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

const empty = { title: "", excerpt: "", body: "", tags: "", reference_topic: "", cover_url: "" };

export default function Editor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState(empty);
  const [status, setStatus] = useState("draft");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    api(`/api/v1/posts/${id}`)
      .then((post) => {
        setStatus(post.status);
        setForm({
          title: post.title,
          excerpt: post.excerpt,
          body: post.body,
          tags: post.tags.join(", "),
          reference_topic: post.reference_topic || "",
          cover_url: post.cover_url || "",
        });
      })
      .catch((err) => setError(err.message));
  }, [id]);

  function update(event) {
    setForm({ ...form, [event.target.name]: event.target.value });
  }

  function payload() {
    return {
      title: form.title,
      body: form.body,
      excerpt: form.excerpt || null,
      tags: form.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      cover_url: form.cover_url || null,
      reference_topic: form.reference_topic || null,
    };
  }

  async function save(publish) {
    setBusy(true);
    setError("");
    try {
      let post;
      if (!id) {
        post = await api(`/api/v1/posts?publish=${publish ? "true" : "false"}`, {
          method: "POST",
          body: payload(),
        });
      } else {
        post = await api(`/api/v1/posts/${id}`, { method: "PUT", body: payload() });
        if (publish && post.status !== "published") {
          post = await api(`/api/v1/posts/${id}/publish`, { method: "POST" });
        }
        if (!publish && status === "published") {
          post = await api(`/api/v1/posts/${id}/unpublish`, { method: "POST" });
        }
      }
      navigate(post.status === "published" ? `/posts/${post.slug}` : "/me");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function upload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const result = await api("/api/v1/uploads/cover", { method: "POST", form: formData });
      setForm((current) => ({ ...current, cover_url: result.cover_url }));
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
      <label>
        Title
        <input name="title" value={form.title} onChange={update} required minLength={3} />
      </label>
      <label>
        Excerpt
        <input name="excerpt" value={form.excerpt} onChange={update} placeholder="Optional. Otherwise the opening is used." />
      </label>
      <label>
        Body
        <textarea name="body" value={form.body} onChange={update} rows={14} required />
      </label>
      <label>
        Tags
        <input name="tags" value={form.tags} onChange={update} placeholder="engineering, rest" />
      </label>
      <label>
        Reference topic
        <input
          name="reference_topic"
          value={form.reference_topic}
          onChange={update}
          placeholder="Optional Wikipedia lookup, for example HTTP"
        />
      </label>
      <label>
        Cover image
        <input type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={upload} />
      </label>
      {form.cover_url && <img className="cover-preview" src={form.cover_url} alt="" />}
      {error && <p className="error">{error}</p>}
      <div className="actions">
        <button type="button" className="button ghost" disabled={busy} onClick={() => save(false)}>
          Save draft
        </button>
        <button type="button" className="button" disabled={busy} onClick={() => save(true)}>
          Publish
        </button>
        {id && (
          <button type="button" className="text-button danger" onClick={remove}>
            Delete
          </button>
        )}
      </div>
    </section>
  );
}
