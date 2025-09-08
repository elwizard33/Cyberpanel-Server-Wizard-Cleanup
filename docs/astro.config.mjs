import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// GitHub Pages project site settings
const repo = 'Cyberpanel-Server-Wizard-Cleanup';
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
          label: 'Guide',
          autogenerate: { directory: '.' }
        }
      ]
    })
  ]
});
