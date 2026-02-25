const footerText = document.getElementById('footer-text');
const routePathContainer = document.getElementById('route-path');
const currentYear = new Date().getFullYear();
footerText.textContent = `© 2003 / ${currentYear} Marcos Reyes / Lain Iwakura. All rights reserved.`;

const normalizePath = (path) => {
    if (!path) {
        return '/';
    }

    if (path.length > 1 && path.endsWith('/')) {
        return path.slice(0, -1);
    }

    return path;
};

const route = normalizePath(window.location.pathname);

const staticRoutes = [
    { path: '/about', label: 'About Website' },
    { path: '/markus-tech-stack', label: 'Markus Tech Stack' },
    { path: '/portfolio', label: 'Portfolio' }
];

const normalizedStaticRoutes = staticRoutes.map((item) => ({
    ...item,
    path: normalizePath(item.path)
}));

const buttonsWrapper = document.createElement('div');

if (route === '/') {
    const routesTitle = document.createElement('h4');
    routesTitle.textContent = 'Available routes';
    buttonsWrapper.appendChild(routesTitle);

    normalizedStaticRoutes.forEach((item) => {
        const link = document.createElement('a');
        link.href = item.path;
        link.textContent = item.label;
        link.className = 'route-button';
        buttonsWrapper.appendChild(link);
    });
} else {
    const homeLink = document.createElement('a');
    homeLink.href = '/';
    homeLink.textContent = 'Back Home';
    homeLink.className = 'route-button';
    buttonsWrapper.appendChild(homeLink);
}

if (routePathContainer) {
    routePathContainer.appendChild(buttonsWrapper);
}