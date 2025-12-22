# QA Checklist (Smoke Test)

## Before merging to main
- [ ] CI is green (lint + tests)
- [ ] `pytest -q` passes locally (optional)
- [ ] No secrets committed (keys/tokens/passwords)

## After Render deploy
- [ ] Open `/` returns 200
- [ ] Open `/docs` loads Swagger UI
- [ ] Basic flow sanity: (fill as features are added)
