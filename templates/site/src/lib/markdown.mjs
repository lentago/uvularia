// A tiny, escape-first Markdown renderer for record bodies.
//
// WHY NOT A LIBRARY. "No new dependencies beyond Astro" (task constraint), and a
// record body is plain prose with light formatting. This renders a conservative,
// safe subset: ATX headings, paragraphs, bullet and numbered lists, blockquotes,
// fenced code, and inline **bold** / *italic* / `code` / [text](url). It ESCAPES
// all HTML first, so a record body can never inject markup into the site — only
// the recognised Markdown shapes become tags. Anything fancier renders as its
// literal text, which is the safe failure.

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inline(s) {
  // Operates on already-escaped text. Order matters: code spans first so their
  // contents are not re-processed.
  let out = s.replace(/`([^`]+)`/g, (_m, c) => `<code>${c}</code>`);
  out = out.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_m, text, href) => {
    // href is already HTML-escaped; only allow http(s), mailto, and relative.
    if (/^(https?:|mailto:|\/|\.|#)/i.test(href)) return `<a href="${href}">${text}</a>`;
    return `${text} (${href})`;
  });
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
  return out;
}

export function renderMarkdown(src, { dropFirstH1 = false } = {}) {
  const lines = escapeHtml(src.replace(/\r\n/g, "\n")).split("\n");
  const html = [];
  let para = [];
  let list = null; // "ul" | "ol"
  let inCode = false;
  let code = [];
  let droppedH1 = false;

  const flushPara = () => {
    if (para.length) {
      html.push(`<p>${inline(para.join(" "))}</p>`);
      para = [];
    }
  };
  const flushList = () => {
    if (list) {
      html.push(`</${list}>`);
      list = null;
    }
  };

  for (const line of lines) {
    if (inCode) {
      if (line.trim().startsWith("```")) {
        html.push(`<pre><code>${code.join("\n")}</code></pre>`);
        code = [];
        inCode = false;
      } else {
        code.push(line);
      }
      continue;
    }
    if (line.trim().startsWith("```")) {
      flushPara();
      flushList();
      inCode = true;
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      flushPara();
      flushList();
      const level = heading[1].length;
      if (dropFirstH1 && level === 1 && !droppedH1) {
        droppedH1 = true; // the page shows the title itself; skip the body's H1
        continue;
      }
      html.push(`<h${level}>${inline(heading[2].trim())}</h${level}>`);
      continue;
    }

    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+\.\s+(.*)$/);
    if (bullet || numbered) {
      flushPara();
      const want = bullet ? "ul" : "ol";
      if (list !== want) {
        flushList();
        html.push(`<${want}>`);
        list = want;
      }
      html.push(`<li>${inline((bullet || numbered)[1].trim())}</li>`);
      continue;
    }

    const quote = line.match(/^>\s?(.*)$/);
    if (quote) {
      flushPara();
      flushList();
      html.push(`<blockquote>${inline(quote[1].trim())}</blockquote>`);
      continue;
    }

    if (line.trim() === "") {
      flushPara();
      flushList();
      continue;
    }

    para.push(line.trim());
  }
  flushPara();
  flushList();
  if (inCode) html.push(`<pre><code>${code.join("\n")}</code></pre>`);
  return html.join("\n");
}
