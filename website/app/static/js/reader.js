/* Blog post and portfolio project pages (main/blog_post*.html,
   main/portfolio_detail*.html): reading progress bar, table of contents
   and copy buttons on code blocks.
   The page scrolls the window here (not .main-content as in base.html), so
   TOC links are plain #anchors and .prose headings carry scroll-margin-top. */
(function () {
    var article = document.querySelector('.article');
    if (!article) return;
    var prose = article.querySelector('.prose');

    /* ── Table of contents ── */
    var toc = document.getElementById('toc');
    var tocList = document.getElementById('toc-list');
    var details = toc.querySelector('details');
    var wide = window.matchMedia('(min-width: 1300px)');
    var headings = Array.prototype.slice.call(prose.querySelectorAll('h1, h2, h3'));
    var links = [];

    var usedIds = {};
    function slugify(text) {
        var base = text.toLowerCase()
            .replace(/[^\w\s\-áéíóúüñàèìòùâêîôûäëïöü]/g, '')
            .trim()
            .replace(/[\s_]+/g, '-')
            .replace(/-+/g, '-') || 'heading';
        var id = base;
        var n = 1;
        while (usedIds[id] || document.getElementById(id)) { id = base + '-' + (++n); }
        usedIds[id] = true;
        return id;
    }

    if (headings.length) {
        var minLevel = Math.min.apply(null, headings.map(function (h) { return +h.tagName.charAt(1); }));
        headings.forEach(function (h) {
            if (!h.id) h.id = slugify(h.textContent.trim());
            var li = document.createElement('li');
            li.setAttribute('data-depth', +h.tagName.charAt(1) - minLevel);
            var a = document.createElement('a');
            a.href = '#' + h.id;
            a.textContent = h.textContent.trim();
            li.appendChild(a);
            tocList.appendChild(li);
            links.push(a);
        });
        toc.hidden = false;
        details.open = wide.matches;

        /* inline (narrow) TOC sits above the text: fold it before the browser
           jumps, so the jump lands on the heading and not a panel-height off */
        tocList.addEventListener('click', function (e) {
            if (e.target.closest('a') && !wide.matches) details.open = false;
        });
    }

    /* ── Progress bar + active TOC entry ── */
    var progress = document.getElementById('read-progress');
    var ticking = false;

    function update() {
        ticking = false;
        var max = document.documentElement.scrollHeight - window.innerHeight;
        if (progress) progress.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, window.scrollY / max) : 0) + ')';

        var active = -1;
        for (var i = 0; i < headings.length; i++) {
            if (headings[i].getBoundingClientRect().top <= 96) active = i;
        }
        links.forEach(function (a, i) { a.classList.toggle('is-active', i === active); });
    }

    window.addEventListener('scroll', function () {
        if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener('resize', update);
    update();

    /* ── Copy buttons on code blocks ── */
    var copyLabel = article.getAttribute('data-copy');
    var copiedLabel = article.getAttribute('data-copied');

    function fallbackCopy(text) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(ta);
    }

    prose.querySelectorAll('pre').forEach(function (pre) {
        var code = pre.querySelector('code');
        if (!code) return;

        var wrap = document.createElement('div');
        wrap.className = 'code-block-wrap';
        pre.parentNode.insertBefore(wrap, pre);
        wrap.appendChild(pre);

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'code-copy-btn';
        btn.textContent = copyLabel;
        wrap.appendChild(btn);

        btn.addEventListener('click', function () {
            var text = code.textContent;
            var done = function () {
                btn.textContent = copiedLabel;
                btn.classList.add('copied');
                setTimeout(function () {
                    btn.textContent = copyLabel;
                    btn.classList.remove('copied');
                }, 1500);
            };
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(done, function () {
                    fallbackCopy(text);
                    done();
                });
            } else {
                fallbackCopy(text);
                done();
            }
        });
    });
})();
