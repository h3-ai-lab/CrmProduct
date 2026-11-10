# Dino CRM Manual Maintenance

This project owns the bilingual CRM handbook served at:

`http://127.0.0.1:58078/preview/p1/index.html`

The URL is a stable WorkBuddy preview mapped to `dist/`. Preserve it. Do not create a new preview URL or move the published entry file.

The manual is maintained locally only. Do not add or restore GitHub, GitLab or other remote deployment workflows unless the user explicitly requests publishing.

When the user announces a requirement is live:

1. Read the linked PRD and the current Chinese/English manual pages.
2. Compare the live product behavior with the manual; identify affected pages from the current menu structure and screenshots.
3. Update both `docs/` and `docs/en/` in the same change. A feature is not complete if only one language is updated.
4. Use official feature names and reflect current UI behavior. Do not document planned behavior as live.
5. Build a new immutable release with `python3 build.py --release <version> ...`.
6. Verify the stable current URL, the English page, the version history page, and the archived version.
7. Report changed pages, version number, verification results, and unresolved issues.

Version rules:

- Never overwrite an existing version.
- `dist/index.html` always serves the latest version at the stable URL.
- Historical snapshots live in `releases/<version>/site/` and are published under `dist/versions/<version>/`.
- The history index is `dist/versions/index.html`.
- Source screenshots must be versioned through the generated release snapshot.

Documentation must describe what users can do now. If a PRD and the released product differ, document the released product and report the discrepancy.

