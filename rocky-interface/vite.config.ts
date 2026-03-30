import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, '.', '');

	if (mode === 'production') {
		return {
			plugins: [sveltekit()]
		};
	}

	const host = env.VITE_DEV_HOST?.trim();
	if (!host) {
		throw new Error('Missing required env var: VITE_DEV_HOST');
	}

	const rawPort = env.VITE_DEV_PORT?.trim();
	if (!rawPort) {
		throw new Error('Missing required env var: VITE_DEV_PORT');
	}

	const port = Number(rawPort);
	if (!Number.isInteger(port) || port < 1 || port > 65535) {
		throw new Error(`Invalid VITE_DEV_PORT: "${rawPort}". Expected an integer between 1 and 65535.`);
	}

	const rawAllowedHosts = env.VITE_ALLOWED_HOSTS?.trim();
	if (!rawAllowedHosts) {
		throw new Error('Missing required env var: VITE_ALLOWED_HOSTS');
	}

	const allowedHosts = rawAllowedHosts
		.split(',')
		.map((entry) => entry.trim())
		.filter((entry) => entry.length > 0);

	if (allowedHosts.length === 0) {
		throw new Error('Invalid VITE_ALLOWED_HOSTS: provide at least one host, e.g. "localhost,127.0.0.1".');
	}

	return {
		plugins: [sveltekit()],
		server: {
			allowedHosts,
			host,
			port
		}
	};
});
