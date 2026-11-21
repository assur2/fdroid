"""Verify corresponding sources in the signed v2 catalog and link them on the download page."""
import hashlib
import json
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

repo = Path(sys.argv[1])
index = json.loads((repo / "index-v2.json").read_text())
links = []
for app in index["packages"].values():
    name = escape(app["metadata"]["name"]["en-US"])
    versions = sorted(app["versions"].values(), key=lambda v: -v["manifest"]["versionCode"])
    for version in versions:
        source = version["src"]
        path = repo / source["name"].lstrip("/")
        assert path.name == Path(version["file"]["name"]).stem + "_src.tar.gz"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
        label = escape(version["manifest"]["versionName"])
        links.append(f'<li><a href="{quote(path.name)}" download><strong>{name} {label}</strong>'
                     '<span>Download .tar.gz</span></a></li>')
page = repo / "index.html"
html = page.read_text()
assert html.count("</body>") == html.count("</head>") == 1
html = html.replace("</head>", '<link rel="stylesheet" href="../release-sources.css">\n</head>')
section = ('<section id="release-sources" aria-labelledby="source-title"><h2 id="source-title">'
           'Release source code</h2><ul>' + ''.join(links) + '</ul></section>')
page.write_text(html.replace("</body>", section + "\n</body>"))

