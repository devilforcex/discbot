# Landing Page Implementation Plan

## Goals
- Transform existing index.html into a standalone landing page for the DiscBot.
- Serve it at a dedicated address (e.g., http://localhost:8080 or configurable port).
- Keep all changes within the `bot/` directory structure.

## Steps
- [ ] Analyze current `index.html` and extract dependencies (CSS, JS, images).
- [ ] Create a minimal routing endpoint in `dashboard.py`/`routes.py` to serve the landing page.
- [ ] Adjust relative links and asset paths to work from the new location.
- [ ] Ensure the landing page is accessible at the target address.
- [ ] Test locally and verify functionality.
- [ ] Document any required environment variables or configuration.

## Details
1. **Asset Relocation**
   - Move `index.html` into `bot/dashboard/static/landing/` (or similar).
   - Copy required assets (`docs/assets/*.png`, `static/css/*`, `static/js/*`) into the landing directory or keep them in existing locations with relative references.

2. **Routing**
   - Add a new route in `routes.py` (e.g., `@app.get("/")`) that returns the landing page.
   - Ensure the route is mounted correctly in `dashboard.py`.

3. **Configuration**
   - Determine the target port (e.g., 3000) and update the server startup to expose it.
   - Optionally allow the port to be configured via environment variable.

4. **Testing**
   - Run the server and verify that the landing page is reachable at `http://localhost:<port>`.
   - Check that all assets load correctly and that navigation links work.

5. **Deployment**
   - If the target address is external, consider using a tunneling service (e.g., ngrok) that forwards to the local port.
   - Ensure the tunnel URL is shared with stakeholders.

## Risks & Mitigations
- **Asset Path Issues**: Update all relative URLs to reflect the new directory structure.
- **Port Conflicts**: Choose a port that is not already in use (e.g., 3000 or 8080).
- **Security**: Since the landing page is static, ensure no sensitive information is exposed.