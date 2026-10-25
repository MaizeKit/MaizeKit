// @ts-check
// MaizeKit documentation, built with Starlight. Pages in src/content/docs are generated
// from the kit by ../tools/build_docs.py; this file only sets the layout and navigation.
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
	site: 'https://maizekit.github.io',
	base: '/docs',
	outDir: '../_site/docs',
	integrations: [
		starlight({
			title: 'MaizeKit',
			logo: { src: './src/assets/maizekit-icon.svg' },
			favicon: '/favicon.svg',
			customCss: ['./src/styles/maizekit.css'],
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/MaizeKit/MaizeKit' }],
			sidebar: [
				{ label: 'Essentials', items: ['getting-started', 'configuration'] },
				{ label: 'Visitors', items: ['errors', 'settings'] },
				{ label: 'Contributing', items: ['reference', 'build-tool'] },
			],
		}),
	],
});
