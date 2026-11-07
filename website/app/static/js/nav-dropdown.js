document.addEventListener('DOMContentLoaded', () => {
    const dropdowns = document.querySelectorAll('.nav-dropdown');
    if (!dropdowns.length) return;

    const closeAll = () => {
        dropdowns.forEach((dropdown) => {
            dropdown.classList.remove('open');
            dropdown.querySelector('.nav-dropdown-toggle')?.setAttribute('aria-expanded', 'false');
        });
    };

    dropdowns.forEach((dropdown) => {
        const toggle = dropdown.querySelector('.nav-dropdown-toggle');
        if (!toggle) return;

        toggle.setAttribute('aria-expanded', 'false');

        toggle.addEventListener('click', (event) => {
            event.preventDefault();
            const wasOpen = dropdown.classList.contains('open');
            closeAll();
            if (!wasOpen) {
                dropdown.classList.add('open');
                toggle.setAttribute('aria-expanded', 'true');
            }
        });
    });

    document.addEventListener('click', (event) => {
        dropdowns.forEach((dropdown) => {
            if (!dropdown.contains(event.target)) {
                dropdown.classList.remove('open');
                dropdown.querySelector('.nav-dropdown-toggle')?.setAttribute('aria-expanded', 'false');
            }
        });
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeAll();
    });
});
