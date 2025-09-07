import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://elwizard33.github.io/Cyberzard',
  base: '/Cyberzard/',
  markdown: {
    shikiConfig: {
      theme: 'github-dark'
    }
  }
});
