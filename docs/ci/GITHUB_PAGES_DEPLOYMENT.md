# GitHub Pages deployment prerequisites

The Pages workflow validates the static site on pull requests and deploys only from `main`.

If `actions/configure-pages` reports `Get Pages site failed: Not Found`, the repository has no Pages site configured yet. One-time setup requires a repository administrator:

1. Open **Settings → Pages** for `amerhwitat/ChimeraIIOS`.
2. Set **Build and deployment → Source** to **GitHub Actions**, then save.
3. Ensure the Actions workflow token has Pages write and ID-token write permissions.
4. Re-run the deployment workflow from `main`.

For automatic first-time enablement, configure a repository Actions secret named `PAGES_ADMIN_TOKEN` containing a least-privilege token that has permission to administer this repository's Pages settings. The workflow prefers that token and falls back to `GITHUB_TOKEN`; GitHub may require the administrator action above if the fallback token cannot enable Pages.

Do not put tokens in workflow source, commit them, or expose them in logs. A successful PR validation is not a deployed website; deployment is confirmed only by a successful deploy job and its published page URL.
