"""Add the latest public Windows download to the Pages artifact."""
import re
from pathlib import Path

site = Path("site")
releases = []
for archive in (site / "windows/notes").glob("v*/Notes-Windows-x64.zip"):
    match = re.fullmatch(r"v(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})", archive.parent.name)
    if match:
        releases.append((tuple(map(int, match.groups())), archive))

_, latest = max(releases)
version = latest.parent.name[1:]
href = "../" + latest.relative_to(site).as_posix()
size = round(latest.stat().st_size / 1024**2)
section = f'''<section id="windows-download" aria-labelledby="windows-title">
<h2 id="windows-title">Notes for Windows</h2>
<ul><li><a href="{href}" download><strong>Notes {version} · Windows x64</strong>
<span>Download ZIP ({size} MiB)</span></a></li></ul>
<p>Extract the ZIP and open <strong>Notes.exe</strong>. Java is included.</p>
</section>
'''
page = site / "repo/index.html"
html = page.read_text(encoding="utf-8")
marker = '<section id="release-sources"'
if html.count(marker) != 1:
    raise ValueError("Expected one source downloads panel in the F-Droid page")
page.write_text(html.replace(marker, section + marker), encoding="utf-8")
