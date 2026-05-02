# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Site Overview

This is the **Rochester BEAR Lab** (Behavioral Enhancement and Adaptive Reality) academic website, built with Jekyll and deployed via GitHub Pages to `augmented-perception.org`. It is a static site with no backend.

## Development Commands

```bash
# Install dependencies (first time)
gem install jekyll bundler
bundle install
npm install

# Serve locally with live reload
npm start
# On Windows, use: bundle exec jekyll serve --livereload --force-polling

# Format all HTML, SCSS, YAML, and Markdown with Prettier
npm run fix
```

The built site is output to `_site/` (git-ignored). Deployment is automatic via GitHub Actions on push to `main` — the workflow builds Jekyll and publishes `_site/` to the `gh-pages` branch.

## Architecture

**Jekyll collections** drive most content:
- `_publications/` — one `.html` file per paper; front matter carries metadata (title, authors, venue, year, thumbnail, links). Published as individual pages.
- `_posts/` — lab news posts.
- `_data/people.yml` and `_data/alumni.yml` — YAML arrays that drive the team page. No HTML file needed per person; rendered via `_includes/person/`.

**Layouts** (`_layouts/`): `default.html` is the root shell; all pages use it directly or through `page.html`, `publication.html`, `course.html`, or `post.html`.

**Styling**: Tachyons utility CSS (loaded from `node_modules/tachyons-sass`) plus custom overrides in `styles.scss`. Avoid writing new CSS when Tachyons utility classes can do the job.

**Publication filtering**: `_includes/pubfilter.js` and `_includes/itemsjs.min.js` power client-side filtering on `publications.html`. No server-side logic.

## Content Update Patterns

**Adding a team member**: append an entry to `_data/people.yml` with fields `name`, `role`, `bio`, `photo`, `website`, etc. Place their photo in `assets/people/`. Alumni go in `_data/alumni.yml` with an `alumni_since` field.

**Adding a publication**: create a new file in `_publications/` (copy an existing one as a template). Required front matter: `title`, `authors`, `venue`, `year`, `thumbnail`. Place the thumbnail image in `assets/publications/`.

**Jekyll config**: `_config.yml` defines collections, plugins (jekyll-seo-tag, jekyll-sitemap, jekyll-external-links, jekyll-redirect-from, jekyll-mentions), and site metadata.

## Formatting

Prettier is configured (`.prettierrc`) with 2-space indentation for HTML, SCSS, YAML, and Markdown. Run `npm run fix` before committing to keep formatting consistent.
