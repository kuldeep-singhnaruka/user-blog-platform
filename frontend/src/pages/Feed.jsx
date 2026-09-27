import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { coverFor, coverStyle } from "../covers";
import { formatWhen, people, posterTone } from "../format";

export default function Feed() {
  const [params, setParams] = useSearchParams();
  const [page, setPage] = useState(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(params.get("q") || "");
  const q = params.get("q") || "";
  const author = params.get("author") || "";
  const sort = params.get("sort") === "oldest" ? "oldest" : "newest";
  const pageNumber = Number(params.get("page") || "1");

  useEffect(() => {
    const search = new URLSearchParams();
    if (q) search.set("q", q);
    if (author) search.set("author", author);
    search.set("sort", "published_at");
    search.set("order", sort === "oldest" ? "asc" : "desc");
    search.set("page", String(pageNumber));
    search.set("page_size", "12");
    setError("");
    api(`/api/v1/posts?${search.toString()}`, { auth: false })
      .then(setPage)
      .catch((err) => setError(err.message));
  }, [q, author, sort, pageNumber]);

  function update(next) {
    const merged = { q, author, sort, page: "1", ...next };
    const clean = {};
    Object.entries(merged).forEach(([key, value]) => {
      if (value && !(key === "sort" && value === "newest") && !(key === "page" && value === "1")) {
        clean[key] = value;
      }
    });
    setParams(clean);
  }

  const posts = page?.data ?? [];
  const showLead = !q && !author && pageNumber === 1 && posts.length > 0;
  const lead = showLead ? posts[0] : null;
  const rest = lead ? posts.slice(1) : posts;

  return (
    <section>
      <form
        className="find"
        onSubmit={(event) => {
          event.preventDefault();
          update({ q: query.trim(), page: "1" });
        }}
      >
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Find a note"
          aria-label="Search"
        />
        <button className="button square" type="submit">Find</button>
        <div className="sorts">
          <button type="button" className={sort === "newest" ? "on" : ""} onClick={() => update({ sort: "newest", page: "1" })}>
            Newest
          </button>
          <button type="button" className={sort === "oldest" ? "on" : ""} onClick={() => update({ sort: "oldest", page: "1" })}>
            Oldest
          </button>
        </div>
      </form>
      {author && (
        <p className="filter-note">
          Showing <strong>{author}</strong>
          <button type="button" onClick={() => update({ author: "", page: "1" })}>Clear</button>
        </p>
      )}
      {error && <p className="error">{error}</p>}
      {!page && !error && <p className="muted">Opening the field…</p>}
      {page && posts.length === 0 && <p className="empty">Nothing published matches that.</p>}
      <div className="wall">
        {lead && <Poster post={lead} lead onAuthor={(slug) => update({ author: slug, page: "1" })} />}
        {rest.map((post) => (
          <Poster key={post.id} post={post} onAuthor={(slug) => update({ author: slug, page: "1" })} />
        ))}
      </div>
    </section>
  );
}

function Poster({ post, lead = false, onAuthor }) {
  const tone = posterTone(post.id + (lead ? 1 : 0));
  const cover = coverFor(post.slug);
  return (
    <article className={`poster${lead ? " lead" : ""}${cover ? " has-cover" : ""}`} style={coverStyle(post.slug, tone)}>
      <div>
        {lead && <p className="poster-kicker">Latest note</p>}
        <h2><Link to={`/posts/${post.slug}`}>{post.title}</Link></h2>
        <p className="poster-excerpt">{post.excerpt}</p>
      </div>
      <Meta post={post} onAuthor={onAuthor} />
    </article>
  );
}

function Meta({ post, onAuthor }) {
  return (
    <p className="meta">
      <button type="button" onClick={() => onAuthor(post.blog_slug)}>{post.author_display_name}</button>
      <span>{formatWhen(post.published_at)}</span>
      <span>{people(post.like_count, "like")}</span>
      <span>{people(post.comment_count, "comment")}</span>
    </p>
  );
}
