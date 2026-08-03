# Poster

`poster.pdf` — print-ready, one US Letter page, landscape (11 × 8.5 in).

`poster.html` is the source; to re-render it needs Chromium plus the
fonts EB Garamond, Charis SIL, and Noto Naskh Arabic installed system-wide
(all free; fetched from github.com/google/fonts):

```
chromium --headless --no-pdf-header-footer --print-to-pdf=poster.pdf poster.html
```
