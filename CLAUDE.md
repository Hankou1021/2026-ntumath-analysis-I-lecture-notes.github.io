# Working on these notes

Online lecture notes for NTU Math "Analysis I" (2026 Fall), built with PreTeXt and published to GitHub Pages by `.github/workflows/deploy.yml` on every push to `main`.

## Source of truth

- `tex/analysis-i.tex` is the master copy. Edit this file, not `source/main.ptx`.
- `source/main.ptx` is **generated** from it:
  ```bash
  python3 scripts/tex2ptx.py tex/analysis-i.tex source/main.ptx
  ```
  Always regenerate and commit both files together.

## Weekly update

The owner sends LaTeX for that week's lectures (the offline version). For each update:

1. **Rewrite the lectures so they are clear and easy to follow**, in the same style as the lectures already in `tex/analysis-i.tex`:
   - one `\subsection{YYYYMMDD}\label{ssec:MMDD}` per lecture, inside the right `\section{...}` (start a new `\section` with a `\label{sec:...}` when the course reaches a new topic);
   - put every statement in an environment: `df`, `thm`, `lm`, `prop`, `cl`, `ex`, `exs`, `remark`, `recall`, `question`, `claim`, `goal` and `proof`. Give numbered ones a `\label{def:|thm:|lm:|ex:|rmk:...}` and cite them with `Definition \ref{...}` / `Theorem \ref{...}`;
   - write complete sentences and fill in skipped steps. Say which earlier result each step uses, and fix typos or mistakes in the math. Do not add new material beyond the lecture;
   - **do every calculation explicitly and in detail**: show each intermediate line in a displayed `align*`. That includes substitutions, changes of variables, integration by parts, Taylor expansions, chain/product rule computations, estimates (say where each inequality comes from) and how constants are chosen. Never write "a direct computation shows" or "it is easy to check" in place of the computation;
   - use the macros in the preamble (`\R`, `\N`, `\pr`, `\abs`, `\norm`, `\set`, `\sp`, `\d`, `\loc`, `\coloneqq`, ...). Only use commands that `scripts/tex2ptx.py` handles. If something new is needed, extend the converter.
   - **Improve older proofs too.** When an earlier proof is badly written (skipped calculations, unclear steps, gaps or errors), rewrite it to the same standard in the same update, keeping its label. Mention each rewritten proof in the commit message and in the summary to the owner.
2. Insert the new subsections in chronological order (before the appendix sections `app:sard`, `app:fourier`).
3. Regenerate `source/main.ptx` with the converter and check that it prints no warnings.
4. Test build (needs `pip install -r requirements.txt` in a virtualenv, plus XeLaTeX for the TikZ figures and the PDF):
   `pretext build web` and `pretext build print`. In a sandbox that cannot reach runestone.academy, build a copy of the project with `<stringparams debug.rs.dev="yes"/>` on the web target. Never commit that change.
5. Commit `tex/analysis-i.tex` and `source/main.ptx` with a message like `Add lectures 2026-11-17 and 2026-11-19`.

## Links

- Site: https://chenhanou.github.io/2026-ntumath-analysis-I-lecture-notes.github.io/
- PDF: https://chenhanou.github.io/2026-ntumath-analysis-I-lecture-notes.github.io/analysis-i-notes.pdf
