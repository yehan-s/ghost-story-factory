#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

source venv/bin/activate 2>/dev/null || true

python - <<'PY'
from ghost_story_factory.database import DatabaseManager

with DatabaseManager() as db:
    cities = db.get_cities()
    print("CITIES:", [f"{c.id}:{c.name}({c.story_count})" for c in cities])
    for c in cities:
        stories = db.get_stories_by_city(c.id)
        print(f"CITY {c.name} STORIES:", [f"{s.id}:{s.title}" for s in stories])
        for s in stories:
            print(f"  STORY {s.id}:{s.title} duration={s.estimated_duration_minutes} nodes={s.total_nodes} depth={s.max_depth}")
PY


