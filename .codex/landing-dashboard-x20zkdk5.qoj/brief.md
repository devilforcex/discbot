Objective: Redesign E:\DrusaBoT\index.html as a polished landing page/dashboard for the existing DrusaBoT Windows Discord music bot project.

Target audience: Bulgarian/English-speaking Discord server owners running the bot locally on Windows. The page should feel like a real operational dashboard plus product landing page, not a marketing-only brochure.

Constraints:
- Work only inside E:\DrusaBoT.
- Output path: E:\DrusaBoT\index.html.
- Keep it self-contained: HTML, CSS, and JS in the single index.html unless using already-existing local assets under E:\DrusaBoT\docs\assets or E:\DrusaBoT\bot\dashboard\static.
- Do not install packages.
- Do not modify Python/backend files.
- Preserve any existing project intent: Discord music bot, Lavalink, FastAPI dashboard, Windows local setup.

Aesthetic direction: premium dark operational console with metallic/steel music styling. Use high contrast, restrained color diversity, crisp panels, compact status widgets, and mobile-first responsive layout. Avoid generic purple/blue gradient SaaS look. No nested cards.

Content structure:
1. First viewport: DrusaBoT name, concise value proposition, live-style dashboard status strip, main actions: Start locally, Open dashboard, View commands.
2. Dashboard overview: bot readiness, Lavalink status, queue, latency, guild count, local path E:\DrusaBoT.
3. Feature/workflow section: setup, music controls, library, access/admin.
4. Command reference section with compact searchable/filterable command list.
5. Local operations section: paths, checks, troubleshooting.
6. Footer with project-local notes.

Interaction requirements:
- Search/filter commands client-side.
- Buttons/links should target local dashboard URL http://127.0.0.1:18080 where relevant and anchor sections elsewhere.
- Use existing local images if useful: E:\DrusaBoT\docs\assets\steel-music-bot-logo.png and steel-avatar.png.
- Responsive desktop/mobile. Text must not overflow controls.

Typography: system fonts, compact dashboard scale, strong headings only in hero.

Color direction: near-black graphite base, steel gray, white text, cyan/green/yellow/red status accents, small warm accent for music/energy.

Memorable element: hero should combine product identity with an immediately useful dashboard snapshot, so the landing page also feels operational.

Evaluation focus: visual polish, mobile layout, no text overlap, useful dashboard content, clear CTAs, self-contained functionality.
