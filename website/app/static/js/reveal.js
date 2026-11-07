// Elements with [data-reveal] get .reveal (their hidden/empty start state, see about_me.css) and then .in-view
// once they scroll into view. Without JS or with reduced motion nothing is armed, so everything just shows.
(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('in-view');
            observer.unobserve(entry.target);
        });
    }, { threshold: 0.2 });
    document.querySelectorAll('[data-reveal]').forEach((el) => {
        el.classList.add('reveal');
        observer.observe(el);
    });
})();
