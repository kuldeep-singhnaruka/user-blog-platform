const COVERS = {
  "a-boundary-is-a-feature": "/covers/boundary.jpg",
  "authentication-is-not-authorization": "/covers/auth.jpg",
  "what-a-like-actually-counts": "/covers/like.jpg",
  "a-comment-belongs-to-its-writer": "/covers/comment.jpg",
  "publish-is-the-moment-it-leaves-the-desk": "/covers/publish.jpg",
};

export function coverFor(slug) {
  return COVERS[slug] || "";
}

export function coverStyle(slug, tone) {
  const cover = coverFor(slug);
  if (!cover) return { background: tone.bg, color: tone.fg };
  return {
    backgroundImage: `linear-gradient(180deg, rgba(16, 12, 8, 0.18) 0%, rgba(16, 12, 8, 0.82) 78%), url(${cover})`,
    color: "#f7f1e4",
  };
}
