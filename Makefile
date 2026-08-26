.DEFAULT_GOAL := help

PORT = 8873

# ── Help ──────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  make serve         Start dev server → http://localhost:$(PORT)"
	@echo "  make kill          Kill this project's HTTP server"
	@echo "  make feed          Validate data/posts.json, regenerate feed.xml"
	@echo "  make check         Validate data/posts.json only"
	@echo "  make drafts-clean  Delete consumed drafts (data/drafts/)"
	@echo ""

# ── Dev server ────────────────────────────────────────────────────────────────
# CORS-enabled so the hub popup on localhost:8800 can fetch data/posts.json
# cross-origin, matching what GitHub Pages sends in production.
.PHONY: serve
serve:
	@echo "Serving → http://localhost:$(PORT)"
	@PORT=$(PORT) python3 scripts/serve-cors.py

# ── Kill ──────────────────────────────────────────────────────────────────────
.PHONY: kill
kill:
	@lsof -ti :$(PORT) | xargs kill 2>/dev/null && echo "Stopped server on port $(PORT)" || echo "No server running on port $(PORT)"

# ── Feed ──────────────────────────────────────────────────────────────────────
.PHONY: feed check
feed:
	@python3 scripts/build-feed.py

check:
	@python3 scripts/build-feed.py --check

# ── Drafts ────────────────────────────────────────────────────────────────────
# data/drafts/ is gitignored: the /newsroom command writes candidates there and
# the desk consumes them. Clean up after a publish.
.PHONY: drafts-clean
drafts-clean:
	@rm -rf data/drafts && echo "data/drafts/ removed"
