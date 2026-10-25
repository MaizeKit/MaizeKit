// @ts-check
// The MaizeKit website and docs, built with Starlight. The homepage is src/content/docs/index.mdx;
// the pages under src/content/docs/docs/ are generated from the code by build.py.
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
	site: 'https://maizekit.github.io',
	outDir: '../_site',
	integrations: [
		starlight({
			title: 'MaizeKit',
			logo: { src: './src/assets/maizekit-icon.svg' },
			favicon: '/favicon.svg',
			customCss: ['./src/styles/maizekit.css'],
			head: [
				{ tag: 'meta', attrs: { property: 'og:image', content: 'https://maizekit.github.io/brand/og.png' } },
				{ tag: 'meta', attrs: { property: 'og:image:width', content: '1200' } },
				{ tag: 'meta', attrs: { property: 'og:image:height', content: '630' } },
				{ tag: 'meta', attrs: { name: 'twitter:card', content: 'summary_large_image' } },
			],
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/MaizeKit/MaizeKit' }],
			sidebar: [
				{ label: 'Getting started', link: '/docs/' },
				{ label: 'Configuration', slug: 'docs/configuration' },
				{ label: 'Reference', slug: 'docs/reference' },
			],
		}),
	],
});
