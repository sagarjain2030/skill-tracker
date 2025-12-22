# Release Process

## Branch flow
- Work on `develop`
- Open PR: `develop` -> `main`
- Merge only when CI is green
- Render auto-deploys from `main` after CI passes

## Release steps
1. Update CHANGELOG.md
2. Ensure CI green on PR
3. Merge PR to main
4. Verify production URL + `/docs`
