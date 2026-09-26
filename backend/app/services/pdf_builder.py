"""Small text-only PDF writer so exports do not need a native PDF library."""


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap(lines: list[str], width: int = 90) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        text = line.encode("latin-1", "replace").decode("latin-1")
        if not text:
            wrapped.append("")
            continue
        while len(text) > width:
            wrapped.append(text[:width])
            text = text[width:]
        wrapped.append(text)
    return wrapped or [""]


def build_pdf(lines: list[str]) -> bytes:
    pages_src = _wrap(lines)
    page_chunks = [pages_src[index : index + 42] for index in range(0, len(pages_src), 42)]
    objects: dict[int, bytes] = {}
    next_id = 4
    kids: list[str] = []
    for chunk in page_chunks:
        content_id = next_id
        page_id = next_id + 1
        next_id += 2
        commands = ["BT", "/F1 11 Tf", "14 TL", "54 760 Td"]
        for index, line in enumerate(chunk):
            if index:
                commands.append("T*")
            commands.append(f"({_escape(line)}) Tj")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1")
        objects[content_id] = f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream"
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_id} 0 R /Resources << /Font << /F1 3 0 R >> >> >>"
        ).encode("latin-1")
        kids.append(f"{page_id} 0 R")

    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects[2] = f"<< /Type /Pages /Count {len(page_chunks)} /Kids [{' '.join(kids)}] >>".encode("latin-1")
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"

    max_id = next_id - 1
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_id in range(1, max_id + 1):
        offsets.append(len(output))
        output.extend(f"{object_id} 0 obj\n".encode("latin-1"))
        output.extend(objects[object_id])
        output.extend(b"\nendobj\n")
    xref_at = len(output)
    output.extend(f"xref\n0 {max_id + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for object_id in range(1, max_id + 1):
        output.extend(f"{offsets[object_id]:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        f"trailer << /Size {max_id + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode("latin-1")
    )
    return bytes(output)
