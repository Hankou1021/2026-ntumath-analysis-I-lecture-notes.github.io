# 2026 Fall NTU Math — Analysis I lecture notes

Lecture notes for 臺大數學系「分析一」(蕭欽玉 教授, 2026 Fall), written in [PreTeXt](https://pretextbook.org).

- **Website:** https://chenhanou.github.io/2026-ntumath-analysis-I-lecture-notes.github.io/
- **PDF:** https://chenhanou.github.io/2026-ntumath-analysis-I-lecture-notes.github.io/analysis-i-notes.pdf

## Layout

| Path | What it is |
| --- | --- |
| `source/main.ptx` | The notes themselves |
| `publication/publication.ptx` | Numbering and other presentation settings |
| `project.ptx` | Build targets: `web` (HTML site) and `print` (PDF) |
| `.github/workflows/deploy.yml` | Builds both targets and publishes the site on every push |
| `tex/analysis-i.tex` | The LaTeX version of the notes (XeLaTeX) that `source/main.ptx` is generated from |
| `scripts/tex2ptx.py` | Converter from `tex/analysis-i.tex` to `source/main.ptx` |
| `CLAUDE.md` | The weekly update workflow (for Claude Code sessions) |

## Updating the notes

Edit `tex/analysis-i.tex`, regenerate `source/main.ptx` (below), commit both and push to `main`.
GitHub Actions rebuilds the website and the PDF and publishes them in a few minutes (see the **Actions** tab).

## Regenerating the PreTeXt from LaTeX

```bash
python3 scripts/tex2ptx.py tex/analysis-i.tex source/main.ptx
```

## Building locally (optional)

```bash
pip install -r requirements.txt
pretext build web      # output/web/index.html
pretext view web       # preview in the browser
pretext build print    # output/print/main.pdf (needs XeLaTeX, xeCJK and a Noto CJK TC font)
```
