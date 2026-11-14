#!/usr/bin/env python3
"""Convert the Analysis I LaTeX notes to PreTeXt.

Usage:  python3 scripts/tex2ptx.py notes.tex source/main.ptx

This is a purpose-built converter for these notes (their preamble, macros and
theorem environments), not a general LaTeX-to-PreTeXt tool.
"""
import re
import sys

warnings = []

# ---------------------------------------------------------------- helpers
def strip_comments(s):
    return '\n'.join(re.sub(r'(?<!\\)%.*$', '', l) for l in s.split('\n'))


def match_brace(s, i):
    """s[i] == '{'; return the index just past the matching '}'."""
    depth = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == '{' and (j == 0 or s[j - 1] != '\\'):
            depth += 1
        elif c == '}' and (j == 0 or s[j - 1] != '\\'):
            depth -= 1
            if depth == 0:
                return j + 1
    raise ValueError('unbalanced brace near: ' + s[i:i + 60])


def match_bracket(s, i):
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            depth += 1
        elif s[j] == '}':
            depth -= 1
        elif s[j] == ']' and depth == 0:
            return j + 1
    raise ValueError('unbalanced [')


def find_end(s, env, start):
    """start is just after \\begin{env}; return (content_end, after_end)."""
    pat = re.compile(r'\\(begin|end)\{' + re.escape(env) + r'\}')
    depth = 1
    for m in pat.finditer(s, start):
        depth += 1 if m.group(1) == 'begin' else -1
        if depth == 0:
            return m.start(), m.end()
    raise ValueError('no \\end{%s}' % env)


def xid(label):
    return re.sub(r'[^A-Za-z0-9_-]', '-', label)


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ---------------------------------------------------------------- math
DELIMS = {'abs': (r'\lvert', r'\rvert'), 'norm': (r'\lVert', r'\rVert'),
          'set': (r'\lbrace', r'\rbrace'), 'ags': (r'\langle', r'\rangle'),
          'ceil': (r'\lceil', r'\rceil'), 'floor': (r'\lfloor', r'\rfloor'),
          'gen': ('(', ')')}


def mathfix(m):
    out, i = [], 0
    pat = re.compile(r'\\(abs|norm|set|ags|ceil|floor|gen)\*\s*\{')
    while True:
        mm = pat.search(m, i)
        if not mm:
            out.append(m[i:])
            break
        out.append(m[i:mm.start()])
        b = mm.end() - 1
        e = match_brace(m, b)
        l, r = DELIMS[mm.group(1)]
        out.append(r'\left%s %s \right%s' % (l, mathfix(m[b + 1:e - 1]), r))
        i = e
    m = ''.join(out)
    m = re.sub(r'\\bar(?![A-Za-z])', r'\\overline', m)
    m = re.sub(r'\\(Tilde|tilde)(?![A-Za-z])', r'\\widetilde', m)
    m = re.sub(r'\\hat(?![A-Za-z])', r'\\widehat', m)
    m = re.sub(r'\\oldsum(?![A-Za-z])', r'\\sum', m)
    return m.strip()


def split_rows(m):
    rows, depth, cur, i = [], 0, [], 0
    while i < len(m):
        if m.startswith('\\begin{', i):
            depth += 1
        elif m.startswith('\\end{', i):
            depth -= 1
        if depth == 0 and m.startswith('\\\\', i):
            rows.append(''.join(cur))
            cur = []
            i += 2
            continue
        cur.append(m[i])
        i += 1
    rows.append(''.join(cur))
    return [r for r in rows if r.strip()]


def display(m):
    items = []
    for r in split_rows(m):
        lab = re.search(r'\\label\{([^}]*)\}', r)
        r = re.sub(r'\\label\{[^}]*\}', '', r)
        items.append((mathfix(r), lab.group(1) if lab else None))
    if len(items) == 1 and '&' not in items[0][0].replace(r'\&', ''):
        body, lab = items[0]
        if lab:
            return '<md>\n<mrow xml:id="%s" number="yes">%s</mrow>\n</md>' % (xid(lab), esc(body))
        return '<md>%s</md>' % esc(body)
    out = ['<md>']
    for body, lab in items:
        attrs = ' xml:id="%s" number="yes"' % xid(lab) if lab else ''
        out.append('<mrow%s>%s</mrow>' % (attrs, esc(body)))
    out.append('</md>')
    return '\n'.join(out)


# ---------------------------------------------------------------- inline text
ACCENTS = {"\\`a": 'à', "\\'e": 'é', "\\'a": 'á', '\\"o': 'ö', '\\"u': 'ü', "\\`e": 'è'}


def inline(s):
    s = re.sub(r"``(.*?)''", lambda m: '\x01' + m.group(1) + '\x02', s, flags=re.S)
    s = s.replace('---', '\x03')
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == '$':
            j = s.index('$', i + 1)
            out.append('<m>%s</m>' % esc(mathfix(s[i + 1:j])))
            i = j + 1
            continue
        if c == '\\':
            for k, v in ACCENTS.items():
                if s.startswith(k, i):
                    out.append(v)
                    i += len(k)
                    break
            else:
                m = re.match(r'\\([A-Za-z]+)\*?\s*', s[i:])
                if not m:
                    nxt = s[i + 1:i + 2]
                    if nxt in ',; ':
                        out.append(' ')
                    elif nxt in '&%$#_{}':
                        out.append(esc(nxt))
                    else:
                        warnings.append('odd control symbol ' + s[i:i + 3])
                    i += 2
                    continue
                name = m.group(1)
                j = i + m.end()

                def arg(k):
                    e = match_brace(s, k)
                    return s[k + 1:e - 1], e
                if name in ('textit', 'emph'):
                    a, j = arg(j)
                    out.append('<em>%s</em>' % inline(a))
                elif name == 'textbf':
                    a, j = arg(j)
                    out.append('<alert>%s</alert>' % inline(a))
                elif name == 'textcolor':
                    col, j = arg(j)
                    a, j = arg(j)
                    if col != 'white':
                        out.append('<alert>%s</alert>' % inline(a))
                elif name in ('text', 'textsuperscript'):
                    a, j = arg(j)
                    out.append(inline(a))
                elif name in ('ref', 'eqref', 'cref'):
                    a, j = arg(j)
                    out.append('<xref ref="%s" text="global"/>' % xid(a))
                elif name in ('noindent', 'medskip', 'smallskip', 'bigskip', 'hfill',
                              'newpage', 'small', 'par', 'centering'):
                    pass
                elif name in ('ldots', 'dots'):
                    out.append('…')
                else:
                    warnings.append('unknown text command \\' + name)
                    out.append(esc(m.group(0)))
                i = j
            continue
        if c in '{}':
            i += 1
            continue
        if c == '~':
            out.append('\u00a0')
            i += 1
            continue
        out.append(esc(c))
        i += 1
    t = ''.join(out).replace('\x01', '<q>').replace('\x02', '</q>').replace('\x03', '<mdash/>')
    return re.sub(r'[ \t]*\n[ \t]*', '\n', t)


# ---------------------------------------------------------------- blocks
THEOREM = {'thm': 'theorem', 'lm': 'lemma', 'cl': 'corollary', 'prop': 'proposition',
           'claim': 'claim', 'fact': 'fact', 'pp': 'fact'}
DEFN = {'df': 'definition'}
EXAMPLE = {'ex': 'example', 'question': 'question', 'ques': 'question', 'pbm': 'problem'}
REMARK = {'remark': ('remark', None), 'recall': ('remark', 'Recall'),
          'obs': ('observation', None), 'goal': ('note', 'Goal'), 'app': ('note', 'Application')}
LABELNAME = {'thm': 'Theorem', 'lm': 'Lemma', 'cl': 'Corollary', 'prop': 'Proposition',
             'df': 'Definition', 'ex': 'Example', 'question': 'Question', 'remark': 'Remark',
             'recall': 'Recall', 'supp': 'Supplement', 'exs': 'Exercise', 'proof': 'Proof'}
MATH_ENVS = {'align*', 'align', 'equation*', 'equation', 'gather*'}


class Para:
    def __init__(self):
        self.buf, self.parts = [], []

    def text(self, t):
        self.buf.append(t)

    def flush_text(self):
        if self.buf:
            t = inline(''.join(self.buf))
            self.buf = []
            if t.strip():
                self.parts.append(t)

    def add(self, xml):
        self.flush_text()
        self.parts.append(xml)

    def close(self):
        self.flush_text()
        p = ''.join(self.parts).strip()
        self.parts = []
        return '<p>%s</p>' % p if p else None


def parse_blocks(s, level):
    """level: 'division' (theorems etc. allowed), 'statement' (plain content only),
    'text' (inside an aside)."""
    items = []
    para = Para()

    def flush():
        p = para.close()
        if p:
            items.append(('p', p, None))
    i = 0
    tok = re.compile(r'\\begin\{([^}]*)\}|\\\[|\n[ \t]*\n|\\\\|\\label\{([^}]*)\}|\$')
    while True:
        m = tok.search(s, i)
        if not m:
            para.text(s[i:])
            break
        para.text(s[i:m.start()])
        g = m.group(0)
        if g == '$':
            j = s.index('$', m.end())
            para.text(s[m.start():j + 1])
            i = j + 1
            continue
        if g.startswith('\\label'):
            items.append(('label', m.group(2), None))
            i = m.end()
            continue
        if g == '\\\\' or g.strip() == '':
            flush()
            i = m.end()
            continue
        if g == '\\[':
            j = s.index('\\]', m.end())
            para.add(display(s[m.end():j]))
            i = j + 2
            continue
        env = m.group(1)
        cstart, after = find_end(s, env, m.end())
        content = s[m.end():cstart]
        i = after
        if env in MATH_ENVS:
            para.add(display(content))
            continue
        if env in ('enumerate', 'itemize'):
            para.add(make_list(content, env))
            continue
        if env == 'tikzpicture':
            flush()
            code = '\\begin{tikzpicture}' + content + '\\end{tikzpicture}'
            items.append(('p', '<image width="60%%">\n<latex-image>%s</latex-image>\n</image>' % esc(code), None))
            continue
        if env == 'center':
            flush()
            inner = parse_blocks(content, level)
            if inner.strip():
                items.append(('p', inner, None))
            continue
        opt = None
        if content.lstrip().startswith('['):
            k = content.index('[')
            e = match_bracket(content, k + 1)
            opt, content = content[k + 1:e - 1], content[e:]
        flush()
        items.append(('block', env, (opt, content)))
    flush()
    return render(items, level)


def make_list(content, env):
    parts = re.split(r'\\item(?:\[([^\]]*)\])?', content)
    labels, bodies = parts[1::2], parts[2::2]
    marker = ''
    if env == 'enumerate':
        first = labels[0] if labels and labels[0] else None
        marker = ' marker="(i)"'
        if first and re.fullmatch(r'\(?[0-9]+\)?\.?', first):
            marker = ' marker="(1)"'
        elif (first and not re.fullmatch(r'\(?[ivxl]+\)?\.?', first)
              and re.fullmatch(r'\(?[a-z]\)?\.?', first)):
            marker = ' marker="(a)"'
    tag = 'ol' if env == 'enumerate' else 'ul'
    lis = ['<li>\n%s\n</li>' % parse_blocks(b, 'statement') for b in bodies]
    return '<%s%s>\n%s\n</%s>' % (tag, marker, '\n'.join(lis), tag)


def title_xml(opt):
    return '<title>%s</title>\n' % inline(opt) if opt else ''


def render(items, level):
    out = []
    pending_theorem = None
    for kind, a, b in items:
        if kind == 'label':
            warnings.append('stray label ' + a)
            continue
        if kind == 'p':
            out.append(a)
            pending_theorem = None
            continue
        env, (opt, content) = a, b
        lab = None
        mm = re.match(r'\s*\\label\{([^}]*)\}', content)
        if mm:
            lab, content = mm.group(1), content[mm.end():]
        idattr = ' xml:id="%s"' % xid(lab) if lab else ''
        if env == 'quote':
            out.append('<blockquote>\n%s\n</blockquote>' % parse_blocks(content, 'text'))
            continue
        if level != 'division' and env != 'proof':
            ttl = LABELNAME.get(env, env.capitalize()) + (': ' + opt if opt else '')
            out.append('<aside%s>\n<title>%s</title>\n%s\n</aside>' % (
                idattr, inline(ttl), parse_blocks(content, 'text')))
            continue
        if env == 'proof':
            ref = None
            if opt:
                r = re.fullmatch(r'\s*Proof of (?:Theorem|Lemma|Corollary|Proposition)\s*\\ref\{([^}]*)\}\s*', opt)
                if r:
                    ref, opt = r.group(1), None
            refattr = ' ref="%s"' % xid(ref) if ref else ''
            xml = '<proof%s%s>\n%s%s\n</proof>' % (idattr, refattr, title_xml(opt),
                                                  parse_blocks(content, 'statement'))
            if pending_theorem is not None and not ref and level == 'division':
                out[pending_theorem] = out[pending_theorem].replace('</PROOFSLOT>', xml + '\n</PROOFSLOT>')
            else:
                out.append(xml)
            continue
        pending_theorem = None
        if env in THEOREM or env in DEFN:
            tag = THEOREM.get(env) or DEFN[env]
            out.append('<%s%s>\n%s<statement>\n%s\n</statement>\n</PROOFSLOT>\n</%s>' % (
                tag, idattr, title_xml(opt), parse_blocks(content, 'statement'), tag))
            if env in THEOREM:
                pending_theorem = len(out) - 1
        elif env in EXAMPLE:
            tag = EXAMPLE[env]
            out.append('<%s%s>\n%s%s\n</%s>' % (tag, idattr, title_xml(opt),
                                                parse_blocks(content, 'statement'), tag))
        elif env == 'exs':
            out.append('<exercise%s>\n%s<statement>\n%s\n</statement>\n</exercise>' % (
                idattr, title_xml(opt), parse_blocks(content, 'statement')))
        elif env in REMARK:
            tag, fixed = REMARK[env]
            ttl = ('%s: %s' % (fixed, opt) if opt else fixed) if fixed else opt
            out.append('<%s%s>\n%s%s\n</%s>' % (tag, idattr, title_xml(ttl),
                                                parse_blocks(content, 'statement'), tag))
        elif env == 'supp':
            # unnumbered, in the normal text flow (not an <aside>), so numbering matches the PDF
            out.append('<paragraphs%s>\n<title>Supplement</title>\n%s\n</paragraphs>' % (
                idattr, parse_blocks(content, 'statement')))
        elif env == 'todo':
            out.append('<aside%s>\n<title>TODO</title>\n%s\n</aside>' % (
                idattr, parse_blocks(content, 'text')))
        else:
            warnings.append('unhandled env ' + env)
    xml = '\n'.join(out)
    return xml.replace('</PROOFSLOT>\n', '').replace('</PROOFSLOT>', '')


# ---------------------------------------------------------------- divisions
def split_cmd(s, cmd):
    pat = re.compile(r'\\' + cmd + r'(\*?)\s*\{')
    ms = list(pat.finditer(s))
    if not ms:
        return s, []
    pre, out = s[:ms[0].start()], []
    for n, m in enumerate(ms):
        e = match_brace(s, m.end() - 1)
        title = s[m.end():e - 1]
        end = ms[n + 1].start() if n + 1 < len(ms) else len(s)
        content = s[e:end]
        lab = None
        mm = re.match(r'\s*\\label\{([^}]*)\}', content)
        if mm:
            lab, content = mm.group(1), content[mm.end():]
        out.append((title, m.group(1), lab, content))
    return pre, out


def division(tag, title, lab, content, subcmds):
    idattr = ' xml:id="%s"' % xid(lab) if lab else ''
    pre, subs = split_cmd(content, subcmds[0]) if subcmds else (content, [])
    parts = ['<%s%s>' % (tag, idattr), '<title>%s</title>' % inline(title)]
    if subs:
        intro_xml = parse_blocks(pre, 'division').strip()
        if intro_xml:
            parts.append('<introduction>\n%s\n</introduction>' % intro_xml)
        for t, star, l, c in subs:
            parts.append(division(subcmds[0], t, l, c, subcmds[1:]))
    else:
        parts.append(parse_blocks(pre, 'division'))
    parts.append('</%s>' % tag)
    return '\n'.join(parts)


MACROS = r'''
\newcommand{\N}{\mathbb{N}}
\newcommand{\Z}{\mathbb{Z}}
\newcommand{\Q}{\mathbb{Q}}
\newcommand{\R}{\mathbb{R}}
\newcommand{\C}{\mathbb{C}}
\newcommand{\F}{\mathbb{F}}
\newcommand{\eps}{\varepsilon}
\newcommand{\pr}{\partial}
\newcommand{\vol}{\mathrm{vol}}
\newcommand{\coloneqq}{\mathrel{:=}}
\newcommand{\eqqcolon}{\mathrel{=:}}
\newcommand{\abs}[1]{\lvert #1\rvert}
\newcommand{\norm}[1]{\lVert #1\rVert}
\newcommand{\set}[1]{\lbrace #1\rbrace}
\newcommand{\ags}[1]{\langle #1\rangle}
'''


def convert(src):
    start = src.index(r'\section*{Introduction}')
    end = src.index(r'\end{CJK}') if r'\end{CJK}' in src else src.index(r'\end{document}')
    body = strip_comments(src[start:end])
    body = re.sub(r'^\\section\*\{Introduction\}(\\label\{[^}]*\})?', r'\\section*{Introduction}', body)
    # macros whose names clash with LaTeX kernel commands are written out
    body = re.sub(r'\\sp(?![A-Za-z])', r'\\operatorname{supp}', body)
    body = re.sub(r'\\loc(?![A-Za-z])', r'\\mathrm{loc}', body)
    body = re.sub(r'\\d(?![A-Za-z])\s*', r'\\,d', body)
    body = re.sub(r'\\MID(?![A-Za-z])', r'\\mathrel{\\Big\\vert}', body)

    # Introduction: flatten the top-level enumerate (list items cannot hold examples)
    intro_end = body.index(r'\section{')
    intro = body[len(r'\section*{Introduction}'):intro_end]
    b0 = intro.index(r'\begin{enumerate}')
    ce, ae = find_end(intro, 'enumerate', b0 + len(r'\begin{enumerate}'))
    inner = re.sub(r'\\item\[([^\]]*)\]', r'\n\n\\textbf{\1} ', intro[b0 + len(r'\begin{enumerate}'):ce])
    intro = intro[:b0] + inner + '\n\n' + intro[ae:]
    rest = body[intro_end:]

    main_part, app_part = rest.split(r'\appendix')
    _, sections = split_cmd(main_part, 'section')
    _, appendices = split_cmd(app_part, 'section')
    subs = ['subsection', 'subsubsection']
    sec_xml = '\n'.join(division('section', t, l, c, subs) for t, s, l, c in sections)
    app_xml = '\n'.join(division('appendix', t, l, c, subs) for t, s, l, c in appendices)

    doc = f'''<?xml version="1.0" encoding="UTF-8"?>
<pretext xml:lang="en-US" xmlns:xi="http://www.w3.org/2001/XInclude">
<docinfo>
<latex-image-preamble>\\usepackage{{tikz}}</latex-image-preamble>
<macros>{esc(MACROS)}</macros>
</docinfo>
<article xml:id="analysis-i">
<title>臺大數學系　分析一</title>
<subtitle>2026 Fall</subtitle>
<frontmatter>
<bibinfo>
<author><personname>蕭欽玉 教授</personname></author>
<date><today/></date>
</bibinfo>
<titlepage>
<titlepage-items/>
</titlepage>
</frontmatter>
<introduction>
{parse_blocks(intro, 'division')}
</introduction>
{sec_xml}
<backmatter>
{app_xml}
</backmatter>
</article>
</pretext>
'''
    return re.sub(r'\n{2,}', '\n', doc)


if __name__ == '__main__':
    src = open(sys.argv[1], encoding='utf-8').read()
    open(sys.argv[2], 'w', encoding='utf-8').write(convert(src))
    for w in sorted(set(warnings)):
        print('WARN', w, file=sys.stderr)
