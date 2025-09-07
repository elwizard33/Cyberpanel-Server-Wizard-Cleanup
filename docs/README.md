# CyberPanel AI Wizard Documentation

Welcome. Use the navigation below to explore.

> Editing: Once the Astro site is added, an "Edit this page" link will point back to these markdown sources for quick contribution.

## Sections
- [Installation](installation.md)
- [Configuration](configuration.md)
- [Commands Reference](commands.md)
- [AI & Agent](ai_and_agent.md)
- [Remediation Workflow](remediation.md)
- [Security Model](security.md)
- [System Architecture](architecture.md)
- [Project Roadmap](roadmap.md)
- [FAQ](faq.md)

---

Quick Start: Start with [Installation](installation.md) then review [Configuration](configuration.md). Need help? Jump to the [FAQ](faq.md).

## Deployment

The repository includes an Astro site scaffold under `docs/site` and a GitHub Pages workflow (`.github/workflows/deploy-docs.yml`). When you push changes to `main` affecting `docs/`, the site will build and publish to the project Pages URL.

### Adjusting for Custom Domain

1. Configure DNS: create a CNAME record pointing your chosen subdomain (e.g. `docs.example.com`) to `elwizard33.github.io`.
2. Edit `docs/site/public/CNAME` and replace the placeholder with exactly your domain name (single line, no protocol).
3. Commit and push; GitHub Pages will provision SSL (may take a few minutes).
4. Update `astro.config.mjs`:
	- Set `site: 'https://docs.example.com'`
	- If using a custom domain at root, you can set `base: '/'`; if keeping under a subpath keep the repo name base.
5. (Optional) Add canonical link tags or redirect logic if migrating from the GitHub Pages default URL.

### Local Preview

```bash
cd docs/site
npm install
npm run dev
```

### Troubleshooting

- 404 after deploy: ensure `base` matches the repository name if not using a custom domain.
- Mixed content warnings: wait for HTTPS certificate issuance or clear cached insecure assets.
- Old content: GitHub Pages caches aggressively; bust with a small commit or use a query string when testing.

Refer to the roadmap for future enhancements (search, versioning, automated navigation). 
