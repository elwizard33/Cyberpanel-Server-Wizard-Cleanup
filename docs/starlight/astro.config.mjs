import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  integrations: [
    starlight({
      title: 'Cyberzard Docs',
      description: 'AI-assisted CyberPanel security CLI documentation',
      social: {
        github: 'https://github.com/elwizard33/Cyberzard'
      },
      sidebar: [
        { label: 'Getting Started', items: [
          { label: 'Introduction', link: '/introduction' },
          { label: 'Installation', link: '/installation' },
          { label: 'Configuration', link: '/configuration' },
          { label: 'Commands', link: '/commands' }
        ]},
        { label: 'Advanced', items: [
          { label: 'AI & Agent', link: '/ai-and-agent' },
          { label: 'Remediation', link: '/remediation' },
          { label: 'Security', link: '/security' },
          { label: 'Architecture', link: '/architecture' },
          { label: 'Roadmap', link: '/roadmap' },
          { label: 'FAQ', link: '/faq' }
        ]}
      ]
    })
  ]
});
