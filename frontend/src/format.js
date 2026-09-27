export function formatWhen(value) {
  if (!value) return "Not published";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

export function readingMinutes(body) {
  const words = (body || "").trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 180));
}

export function authorHandle(name) {
  const first = (name || "author").trim().split(/\s+/)[0];
  return `@${first}`;
}

const POSTERS = [
  { bg: "#14343a", fg: "#f7f1e4" },
  { bg: "#e4572e", fg: "#1a120c" },
  { bg: "#f0c96a", fg: "#1a120c" },
  { bg: "#24352c", fg: "#f7f1e4" },
  { bg: "#3d2b4d", fg: "#f7f1e4" },
];

export function posterTone(id) {
  return POSTERS[Math.abs(Number(id) || 0) % POSTERS.length];
}

export function people(count, noun) {
  if (noun === "person") return count === 1 ? "1 person" : `${count} people`;
  const label = count === 1 ? noun : `${noun}s`;
  return `${count} ${label}`;
}
