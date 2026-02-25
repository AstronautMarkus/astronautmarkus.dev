const footerText = document.getElementById('footer-text');
const endingText = document.getElementById('ending-text');

const endingImagePath = '/static/img/smilleys/laugh3.gif';

const routePathContainer = document.getElementById('route-path');
const localeToggleButton = document.getElementById('locale-toggle-button');
const localeToggleImage = document.getElementById('locale-toggle-image');
const currentYear = new Date().getFullYear();

const footer_text = `© 16-03-2003 / ${currentYear} Marcos Reyes / AstronautMarkusDev. All rights reserved.`;
const ending_text = 'This website is not optimized for responsive design. And will never be.';

const spanish_footer_text = `© 16-03-2003 / ${currentYear} Marcos Reyes / AstronautMarkusDev. Todos los derechos reservados.`;
const spanish_ending_text = 'Este sitio web no está optimizado para diseño responsivo. Y nunca lo estará.';

const normalizePath = (path) => {
    if (!path) {
        return '/';
    }

    if (path.length > 1 && path.endsWith('/')) {
        return path.slice(0, -1);
    }

    return path;
};

const getRouteContext = (pathname) => {
    const normalizedPath = normalizePath(pathname);

    if (normalizedPath === '/es') {
        return {
            locale: 'es',
            localePrefix: '/es',
            route: '/'
        };
    }

    if (normalizedPath.startsWith('/es/')) {
        const routeWithoutPrefix = normalizedPath.slice(3) || '/';

        return {
            locale: 'es',
            localePrefix: '/es',
            route: normalizePath(routeWithoutPrefix)
        };
    }

    return {
        locale: 'en',
        localePrefix: '',
        route: normalizedPath
    };
};

const routeContext = getRouteContext(window.location.pathname);
const route = routeContext.route;
const isSpanish = routeContext.locale === 'es';

if (footerText) {
    footerText.textContent = isSpanish ? spanish_footer_text : footer_text;
}

if (endingText) {
    endingText.textContent = '';

    const endingTextNode = document.createElement('span');
    endingTextNode.textContent = isSpanish ? spanish_ending_text : ending_text;
    endingText.appendChild(endingTextNode);

    const endingImage = document.createElement('img');
    endingImage.src = endingImagePath;
    endingImage.alt = 'Laugh Smilley';
    endingImage.style.marginLeft = '8px';
    endingText.appendChild(endingImage);
}

const getLocaleToggleTargetPath = () => {
    if (isSpanish) {
        return route === '/' ? '/' : route;
    }

    return route === '/' ? '/es' : `/es${route}`;
};

const toggleButtonConfig = {
    en: {
        imagePath: localeToggleButton?.dataset.imageEn,
        imageAlt: 'Español',
        buttonLabel: 'Cambiar a español'
    },
    es: {
        imagePath: localeToggleButton?.dataset.imageEs,
        imageAlt: 'English',
        buttonLabel: 'Change to English'
    }
};

if (localeToggleButton && localeToggleImage) {
    const config = isSpanish ? toggleButtonConfig.es : toggleButtonConfig.en;
    if (config.imagePath) {
        localeToggleImage.src = config.imagePath;
    }
    localeToggleImage.alt = config.imageAlt;
    localeToggleButton.setAttribute('aria-label', config.buttonLabel);

    localeToggleButton.addEventListener('click', () => {
        const targetPath = getLocaleToggleTargetPath();
        const targetUrl = `${targetPath}${window.location.search}${window.location.hash}`;
        window.location.href = targetUrl;
    });
}

const texts = {
    availableRoutes: isSpanish ? 'Rutas disponibles' : 'Available routes',
    backHome: isSpanish ? 'Volver al inicio' : 'Back Home'
};

const staticRoutes = [
    {
        path: '/about',
        label: isSpanish ? 'Acerca del sitio web' : 'About Website'
    },
    {
        path: '/markus-tech-stack',
        label: isSpanish ? 'Tech Stack de Markus' : 'Markus Tech Stack'
    },
    {
        path: '/portfolio',
        label: isSpanish ? 'Portafolio' : 'Portfolio'
    },
    {
        path: '/work-and-experience',
        label: isSpanish ? 'Trabajo y experiencia' : 'Work and Experience'
    }
];

const normalizedStaticRoutes = staticRoutes.map((item) => ({
    ...item,
    path: normalizePath(item.path)
}));

const buildLocalizedPath = (path) => {
    const normalizedTarget = normalizePath(path);

    if (!routeContext.localePrefix) {
        return normalizedTarget;
    }

    if (normalizedTarget === '/') {
        return routeContext.localePrefix;
    }

    return `${routeContext.localePrefix}${normalizedTarget}`;
};

const buttonsWrapper = document.createElement('div');

if (route === '/') {
    const routesTitle = document.createElement('h4');
    routesTitle.textContent = texts.availableRoutes;
    buttonsWrapper.appendChild(routesTitle);

    normalizedStaticRoutes.forEach((item) => {
        const link = document.createElement('a');
        link.href = buildLocalizedPath(item.path);
        link.textContent = item.label;
        link.className = 'route-button';
        buttonsWrapper.appendChild(link);
    });
} else {
    const homeLink = document.createElement('a');
    homeLink.href = buildLocalizedPath('/');
    homeLink.textContent = texts.backHome;
    homeLink.className = 'route-button';
    buttonsWrapper.appendChild(homeLink);
}

if (routePathContainer) {
    routePathContainer.appendChild(buttonsWrapper);
}