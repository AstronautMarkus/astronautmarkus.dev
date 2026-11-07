/* Global image lightbox modal.
 *
 * Any element carrying the `modal-image` class opens the shared modal
 * (markup lives in base/base.html) when clicked. Elements are read like:
 *   data-full  -> full-size image URL (falls back to the element's own
 *                 src/currentSrc for <img>, or the src of an <img> inside it)
 *   data-title -> caption title (falls back to the element's alt for <img>)
 *   data-desc  -> caption description (optional)
 *   data-modal-group -> browse set for prev/next (defaults to "default",
 *                 shared page-wide by every trigger that omits it)
 */
(function () {
    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }

    ready(function () {
        var overlay = document.getElementById('image-modal-overlay');
        var triggers = Array.prototype.slice.call(document.querySelectorAll('.modal-image'));
        if (!overlay || !triggers.length) return;

        var imgEl = document.getElementById('image-modal-img');
        var titleEl = document.getElementById('image-modal-title');
        var descEl = document.getElementById('image-modal-desc');
        var captionEl = document.getElementById('image-modal-caption');
        var counterEl = document.getElementById('image-modal-counter');
        var closeBtn = document.getElementById('image-modal-close');
        var prevBtn = document.getElementById('image-modal-prev');
        var nextBtn = document.getElementById('image-modal-next');

        var groups = {};
        triggers.forEach(function (el) {
            var group = el.getAttribute('data-modal-group') || 'default';
            (groups[group] = groups[group] || []).push(el);
        });

        var activeGroup = [];
        var current = -1;

        function dataFor(el) {
            var innerImg = el.tagName === 'IMG' ? el : el.querySelector('img');
            return {
                full: el.getAttribute('data-full') || (innerImg && (innerImg.currentSrc || innerImg.src)) || '',
                title: el.getAttribute('data-title') || (innerImg && innerImg.alt) || '',
                desc: el.getAttribute('data-desc') || ''
            };
        }

        function show(index) {
            if (index < 0) index = activeGroup.length - 1;
            if (index >= activeGroup.length) index = 0;
            current = index;

            var data = dataFor(activeGroup[current]);
            imgEl.src = data.full;
            imgEl.alt = data.title;
            titleEl.textContent = data.title;
            descEl.textContent = data.desc;
            descEl.style.display = data.desc ? '' : 'none';
            captionEl.style.display = (data.title || data.desc) ? '' : 'none';
            counterEl.textContent = (current + 1) + ' / ' + activeGroup.length;

            var multiple = activeGroup.length > 1;
            prevBtn.style.display = multiple ? '' : 'none';
            nextBtn.style.display = multiple ? '' : 'none';
        }

        function open(group, index) {
            activeGroup = group;
            show(index);
            overlay.classList.add('open');
            document.body.style.overflow = 'hidden';
        }

        function close() {
            overlay.classList.remove('open');
            document.body.style.overflow = '';
            imgEl.src = '';
        }

        triggers.forEach(function (el) {
            if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');

            el.addEventListener('click', function (e) {
                e.preventDefault();
                var group = groups[el.getAttribute('data-modal-group') || 'default'];
                open(group, group.indexOf(el));
            });

            el.addEventListener('keydown', function (e) {
                if (e.key !== 'Enter' && e.key !== ' ') return;
                e.preventDefault();
                el.click();
            });
        });

        closeBtn.addEventListener('click', close);
        prevBtn.addEventListener('click', function () { show(current - 1); });
        nextBtn.addEventListener('click', function () { show(current + 1); });

        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) close();
        });

        document.addEventListener('keydown', function (e) {
            if (!overlay.classList.contains('open')) return;
            if (e.key === 'Escape') close();
            else if (e.key === 'ArrowLeft') show(current - 1);
            else if (e.key === 'ArrowRight') show(current + 1);
        });
    });
})();
