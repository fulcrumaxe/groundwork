"""Keyboard shortcuts with a ? cheat-sheet overlay (I-40).

Single-key jumps would hijack answer fields, so navigation is a
two-key sequence (g then d) plus ? for this sheet. The handler ignores
keystrokes typed into inputs, textareas, selects, and editors.
"""
from __future__ import annotations

SHORTCUTS = (
    ("g then d", "Due queue", "/due"),
    ("g then m", "Modules library", "/modules"),
    ("g then r", "Review history", "/reviews"),
    ("g then t", "Tour", "/tour"),
    ("g then s", "Status", "/status"),
    ("?", "This cheat sheet", ""),
)


def overlay_html() -> str:
    """Cheat-sheet overlay; every page carries it, hidden by default."""
    rows = "".join(
        f"<tr><td><kbd>{keys}</kbd></td><td>{label}</td></tr>"
        for keys, label, _ in SHORTCUTS)
    return ("<div id='shortcuts' hidden>"
            "<h2>Keyboard shortcuts</h2>"
            f"<table class='log'><tr><th>Keys</th><th>Goes to</th></tr>{rows}</table>"
            "<p><small>Press ? to toggle this sheet.</small></p></div>")


def script_js() -> str:
    """Two-key navigation; never fires while typing an answer."""
    targets = "{" + ",".join(
        f"'{keys[-1]}':'{href}'" for keys, _, href in SHORTCUTS
        if keys.startswith("g then")) + "}"
    return f"""
<script>
(function () {{
  var pending = false, timer = null;
  document.addEventListener('keydown', function (e) {{
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' ||
        e.target.isContentEditable) return;
    if (e.key === '?') {{
      var o = document.getElementById('shortcuts');
      if (o) o.hidden = !o.hidden;
      return;
    }}
    var go = {targets};
    if (pending) {{
      pending = false; clearTimeout(timer);
      if (go[e.key]) window.location.href = go[e.key];
      return;
    }}
    if (e.key === 'g') {{
      pending = true;
      timer = setTimeout(function () {{ pending = false; }}, 800);
    }}
  }});
}})();
</script>"""
