# 2026 Fall NTU Math — Analysis I lecture notes

Lecture notes for 臺大數學系「分析一」(蕭欽玉 教授, 2026 Fall), written in [PreTeXt](https://pretextbook.org).

- **Website:** https://hankou1021.github.io/2026-ntumath-analysis-I-lecture-notes.github.io/
- **PDF:** https://hankou1021.github.io/2026-ntumath-analysis-I-lecture-notes.github.io/analysis-i-notes.pdf

## Layout

| Path | What it is |
| --- | --- |
| `source/main.ptx` | The notes themselves |
| `publication/publication.ptx` | Numbering and other presentation settings |
| `project.ptx` | Build targets: `web` (HTML site) and `print` (PDF) |
| `.github/workflows/deploy.yml` | Builds both targets and publishes the site on every push |

## Updating the notes

Edit `source/main.ptx` and push to `main`.
GitHub Actions rebuilds the website and the PDF and publishes them in a few minutes (see the **Actions** tab).

## Building locally (optional)

```bash
pip install -r requirements.txt
pretext build web      # output/web/index.html
pretext view web       # preview in the browser
pretext build print    # output/print/main.pdf (needs XeLaTeX, xeCJK and a Noto CJK TC font)
```
