import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// GitHub Pages project site settings
const repo = 'Cyberzard';
const owner = 'elwizard33';
const site = `https://${owner}.github.io/${repo}`;

export default defineConfig({
  site,
  base: `/${repo}/`,
  integrations: [
    starlight({
      title: 'Cyberzard Docs',
      description: 'AI-assisted CyberPanel security CLI documentation',
      social: { github: 'https://github.com/elwizard33/Cyberzard' },
      sidebar: [
        {
          label: 'Getting Started',
          items: [
            { label: 'Installation', link: '/docs/installation/' },
            { label: 'Commands', link: '/docs/commands/' },
            { label: 'Configuration', link: '/docs/configuration/' },
          ],
        },
        {
          label: 'How it works',
          items: [
            { label: 'AI & Agent', link: '/docs/ai-and-agent/' },
            { label: 'Architecture', link: '/docs/architecture/' },
            { label: 'Remediation', link: '/docs/remediation/' },
            { label: 'Security Model', link: '/docs/security/' },
          ],
        },
        {
          label: 'Project',
          items: [
            { label: 'FAQ', link: '/docs/faq/' },
            { label: 'Roadmap', link: '/docs/roadmap/' },
          ],
        },
      ],
      search: { provider: 'pagefind' },
    })
  ]
});
