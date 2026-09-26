function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

export function renderMarkdown(source) {
  const escaped = escapeHtml(source || "");
  const blocks = escaped.split(/\n{2,}/);
  return blocks
    .map((block) => {
      const lines = block.split("\n");
      if (lines.every((line) => line.startsWith("- "))) {
        const items = lines.map((line) => `<li>${inline(line.slice(2))}</li>`).join("");
        return `<ul>${items}</ul>`;
      }
      if (lines[0].startsWith("### ")) return `<h3>${inline(lines[0].slice(4))}</h3>`;
      if (lines[0].startsWith("## ")) return `<h2>${inline(lines[0].slice(3))}</h2>`;
      return `<p>${lines.map(inline).join("<br />")}</p>`;
    })
    .join("");
}

function inline(text) {
  return text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`(.+?)`/g, "<code>$1</code>");
}
