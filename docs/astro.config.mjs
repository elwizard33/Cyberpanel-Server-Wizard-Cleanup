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
  // Load site-wide style overrides (e.g., tweak TOC width)
  customCss: ['./src/styles/overrides.css'],
      social: [
        { label: 'GitHub', href: 'https://github.com/elwizard33/Cyberzard', icon: 'github' }
      ],
      sidebar: [
        {
          label: 'Getting Started',
          items: [
            { label: 'Installation', link: '/installation/' },
            { label: 'Commands', link: '/commands/' },
            { label: 'Configuration', link: '/configuration/' },
          ],
        },
        {
          label: 'How it works',
          items: [
            { label: 'AI & Agent', link: '/ai-and-agent/' },
            { label: 'Architecture', link: '/architecture/' },
            { label: 'Remediation', link: '/remediation/' },
            { label: 'Security Model', link: '/security/' },
          ],
        },
        {
          label: 'Project',
          items: [
            { label: 'FAQ', link: '/faq/' },
            { label: 'Roadmap', link: '/roadmap/' },
          ],
        },
      ],
    })
  ]
});
