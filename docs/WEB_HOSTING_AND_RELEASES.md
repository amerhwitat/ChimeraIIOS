# Chimera II Web Hosting and Release Strategy

## Free/public options researched

| Platform | Use | Current model | Chimera use |
|---|---|---|---|
| GitHub Pages | static explorer/docs | public repositories supported on GitHub Free | primary static web surface |
| GitHub Actions | builds/artifacts | public repository standard runners are free | Linux/Windows compilation + artifacts |
| Cloudflare Pages | static web/CDN | static asset requests are free; Functions have quotas | secondary static mirror |
| Render | static site / free web service | static sites free; free services have limits | optional web/API prototype |
| Vercel | static/JS/web | Hobby $0 for personal projects | optional frontend mirror |
| Netlify | static/web/functions | Free plan with monthly credit limit | optional frontend mirror |

Official references:

- GitHub Pages: https://docs.github.com/en/pages/getting-started-with-github-pages
- GitHub Actions billing: https://docs.github.com/en/actions/concepts/billing-and-usage
- Cloudflare Pages pricing: https://developers.cloudflare.com/pages/functions/pricing/
- Render free services: https://render.com/docs/free
- Vercel pricing: https://vercel.com/pricing
- Netlify pricing: https://www.netlify.com/pricing/

## What is automated in the repository

`.github/workflows/pages.yml` packages `web/` as a GitHub Pages artifact and deploys it on pushes to `main` once GitHub Pages is enabled for the repository with **GitHub Actions** as its publishing source.

`.github/workflows/chimera-build-matrix.yml` builds/tests Linux and Windows artifacts and uploads them to GitHub Actions.

## Required one-time account/settings actions

External hosting accounts cannot be created or authenticated by the repository automation on the user's behalf, and passwords/API tokens should never be written into source control or returned in documentation.

For GitHub Pages, an administrator/maintainer must enable Pages → Source → GitHub Actions. GitHub documents this as the required configuration step for a custom Pages workflow.

For Render/Cloudflare/Vercel/Netlify, the user can connect the public GitHub repository through the provider's dashboard. Provider-specific deployment tokens, if later needed, belong in repository/environment secrets and must not be committed.

## Release artifacts

The intended public release layout is:

```text
ChimeraIIOS/
├── source/       uncompiled repository source
├── web/          browser explorer
├── docs/         architecture and standards
├── installer/    installer planning/adapters
└── artifacts/
    ├── linux/
    └── windows/
```

The `artifacts/` directory is represented by CI artifacts rather than checked-in binaries so the source repository stays reproducible and small.
