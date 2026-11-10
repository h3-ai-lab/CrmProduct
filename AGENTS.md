# Dino CRM Manual Maintenance

This project owns the bilingual CRM handbook served at:

`http://127.0.0.1:58078/preview/p1/index.html`

The URL is a stable WorkBuddy preview mapped to `dist/`. Preserve it. Do not create a new preview URL or move the published entry file.

The public handbook is published to GitHub Pages from `h3-ai-lab/CrmProduct`.
The current URL is `https://h3-ai-lab.github.io/CrmProduct/`.

When the user announces a requirement is live:

The trigger may arrive as `xxx需求已上线`, including from a separate requirements chat.

1. Locate the matching PRD under `crm-prd/projects/` or use the PRD link supplied by the user.
2. Read the PRD, current Chinese/English manual pages and latest released product behavior.
3. Compare released behavior with the manual; identify affected page IDs from the current menu and screenshots.
4. Update both `docs/` and `docs/en/` in the same change. A feature is not complete if only one language is updated.
5. Add or replace screenshots when the UI changed and remove sensitive production data.
6. Use official feature names and document only behavior confirmed as live.
7. Run `python3 build.py --check`.
8. Create the next immutable release with `python3 build.py --release <version> ...` and record the PRD URL.
9. Commit and push to `main`.
10. Wait for the `Deploy CrmProduct` workflow to succeed.
11. Verify the public home page, English page, version history and archived version.
12. Report requirement name, changed pages, version number, public URL, verification results, and unresolved issues.

Version rules:

- Never overwrite an existing version.
- `dist/index.html` always serves the latest version at the stable URL.
- Historical snapshots live in `releases/<version>/site/` and are published under `dist/versions/<version>/`.
- The history index is `dist/versions/index.html`.
- Source screenshots must be versioned through the generated release snapshot.

Documentation must describe what users can do now. If a PRD and the released product differ, document the released product and report the discrepancy.

