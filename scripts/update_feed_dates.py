#!/usr/bin/env python3
"""Refresh the "Updated" column of the Artsdata feed table in docs/index.html.

Queries kg.artsdata.ca for each graph's current generatedAtTime and rewrites
the matching `<td data-updated="...">` cell. Run daily by
.github/workflows/update-feed-dates.yml.
"""
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

INDEX_HTML = Path(__file__).resolve().parent.parent / "docs" / "index.html"

GRAPHS = {
    "spektrix-calgaryphil": "http://kg.artsdata.ca/capacoa/artsdata-planet-spektrix/spektrix-calgaryphil",
    "nac-events": "http://kg.artsdata.ca/culture-creates/artsdata-planet-nac/nac-events",
    "calendrier-activites": "http://kg.artsdata.ca/culture-creates/artsdata-planet-ville-de-laval/calendrier-activites",
    "culturegaspesie-org": "http://kg.artsdata.ca/culture-creates/artsdata-orion/culturegaspesie-org",
    "scenesfrancophones-ca": "http://kg.artsdata.ca/capacoa/artsdata-planet-scenesfrancophones/scenesfrancophones-ca",
    "tour-bookings": "http://kg.artsdata.ca/culture-creates/artsdata-planet-atc/tour-bookings",
    "visual-media-arts": "http://kg.artsdata.ca/culture-creates/artsdata-planet-osac/visual-media-arts",
}


def fetch_updated_date(graph_uri: str) -> str:
    url = "https://kg.artsdata.ca/entity.jsonld?uri=" + urllib.parse.quote(graph_uri, safe="")
    req = urllib.request.Request(url, headers={"Accept": "application/ld+json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        import json

        data = json.load(response)
    generated_at = data["generatedAtTime"]
    return generated_at[:10]  # YYYY-MM-DD


def main() -> int:
    html = INDEX_HTML.read_text(encoding="utf-8")
    changed = []

    for slug, graph_uri in GRAPHS.items():
        try:
            new_date = fetch_updated_date(graph_uri)
        except Exception as exc:  # noqa: BLE001
            print(f"warning: could not fetch date for {slug}: {exc}", file=sys.stderr)
            continue

        pattern = re.compile(
            r'(<td data-updated="' + re.escape(slug) + r'">)([^<]*)(</td>)'
        )
        match = pattern.search(html)
        if not match:
            print(f"warning: no <td data-updated=\"{slug}\"> found in index.html", file=sys.stderr)
            continue

        if match.group(2) != new_date:
            html = pattern.sub(lambda m: m.group(1) + new_date + m.group(3), html, count=1)
            changed.append((slug, match.group(2), new_date))

    if changed:
        INDEX_HTML.write_text(html, encoding="utf-8")
        for slug, old, new in changed:
            print(f"updated {slug}: {old} -> {new}")
    else:
        print("no date changes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
