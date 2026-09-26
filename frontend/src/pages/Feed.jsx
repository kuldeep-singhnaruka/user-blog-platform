import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";

function hue(title) {
  let value = 0;
  for (const char of title) value = (value * 33 + char.charCodeAt(0)) % 360;
  return value;
}

export default function Feed() {
  const [params, setParams] = useSearchParams();
  const [page, setPage] = useState(null);
  const [tags, setTags] = useState([]);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(params.get("q") || "");

  const q = params.get("q") || "";
  const tag = params.get("tag") || "";
  const author = params.get("author") || "";
  const sort = params.get("sort") || "published_at";
  const pageNumber = Number(params.get("page") || "1");

  useEffect(() => {
    const search = new URLSearchParams();
    if (q) search.set("q", q);
    if (tag) search.set("tag", tag);
    if (author) search.set("author", author);
    search.set("sort", sort);
    search.set("order", sort === "title" ? "asc" : "desc");
    search.set("page", String(pageNumber));
    setError("");
    api(`/api/v1/posts?${search.toString()}`, { auth: false })
      .then(setPage)
      .catch((err) => setError(err.message));
  }, [q, tag, author, sort, pageNumber]);

  useEffect(() => {
    api("/api/v1/tags", { auth: false })
      .then(setTags)
      .catch(() => setTags([]));
  }, []);

  function update(next) {
    const merged = { q, tag, author, sort, page: "1", ...next };
    const clean = {};
    Object.entries(merged).forEach(([key, value]) => {
      if (value) clean[key] = value;
    });
    setParams(clean);
  }

  const showHero = !q && !tag && !author && pageNumber === 1;

  return (
    <section>
      {showHero && (
        <div className="hero">
          <p className="eyebrow">A reading room</p>
          <h1>Notes worth keeping.</h1>
          <p>Anyone can read. Sign in to publish your own notes, or to like and comment on someone else's.</p>
        </div>
      )}

      <form
        className="filters"
        onSubmit={(event) => {
          event.preventDefault();
          update({ q: query.trim(), page: "1" });
        }}
      >
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search published notes"
          aria-label="Search"
        />
        <select value={sort} onChange={(event) => update({ sort: event.target.value, page: "1" })}>
          <option value="published_at">Newest</option>
          <option value="title">Title</option>
        </select>
        <button className="button" type="submit">
          Search
        </button>
      </form>

      <div className="tag-row">
        <button type="button" className={!tag ? "chip on" : "chip"} onClick={() => update({ tag: "", page: "1" })}>
          All
        </button>
        {tags.map((item) => (
          <button
            key={item.name}
            type="button"
            className={tag === item.name ? "chip on" : "chip"}
            onClick={() => update({ tag: item.name, page: "1" })}
          >
            {item.name}
            <span>{item.count}</span>
          </button>
        ))}
      </div>

      {author && (
        <p className="filter-note">
          Showing <strong>{author}</strong>
          <button type="button" onClick={() => update({ author: "", page: "1" })}>
            Clear
          </button>
        </p>
      )}
      {error && <p className="error">{error}</p>}
      {!page && !error && <p className="muted">Loading the shelf…</p>}
      {page && page.data.length === 0 && <p className="empty">Nothing published matches that filter.</p>}

      <div className="cards">
        {page?.data.map((post) => (
          <article key={post.id} className="card">
            <Link to={`/posts/${post.slug}`} className="cover" style={{ "--hue": hue(post.title) }}>
              {post.cover_url ? <img src={post.cover_url} alt="" /> : <span>{post.tags[0] || "note"}</span>}
            </Link>
            <div>
              <p className="meta">
                <button type="button" onClick={() => update({ author: post.blog_slug, page: "1" })}>
                  {post.author_display_name}
                </button>
                <span>{post.like_count} likes</span>
                <span>{post.comment_count} comments</span>
              </p>
              <h2>
                <Link to={`/posts/${post.slug}`}>{post.title}</Link>
              </h2>
              <p>{post.excerpt}</p>
            </div>
          </article>
        ))}
      </div>

      {page && page.meta.total > page.meta.page_size && (
        <div className="pager">
          <button type="button" disabled={pageNumber <= 1} onClick={() => update({ page: String(pageNumber - 1) })}>
            Previous
          </button>
          <span>
            Page {page.meta.page} of {Math.ceil(page.meta.total / page.meta.page_size)}
          </span>
          <button
            type="button"
            disabled={pageNumber * page.meta.page_size >= page.meta.total}
            onClick={() => update({ page: String(pageNumber + 1) })}
          >
            Next
          </button>
        </div>
      )}
    </section>
  );
}
