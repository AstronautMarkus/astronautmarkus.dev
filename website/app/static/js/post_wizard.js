/* post_wizard.js — step wizard for admin/blog/post_form.html.
   Steps are just panels of one form, so any step can be opened and saved at any time.
   Create mode: gallery photos are queued in the browser and uploaded only after the
   post itself was created without errors. Edit mode: admin.js uploads them immediately. */
(function () {
    'use strict';

    var wizard = document.getElementById('post-wizard');
    var form = document.getElementById('post-form');
    if (!wizard || !form) return;

    var msg = wizard.dataset;
    var steps = Array.prototype.slice.call(wizard.querySelectorAll('.wizard-step'));
    var panels = Array.prototype.slice.call(wizard.querySelectorAll('.wizard-panel'));
    var prevBtn = wizard.querySelector('[data-wizard-prev]');
    var nextBtn = wizard.querySelector('[data-wizard-next]');
    var submitBtn = form.querySelector('[type="submit"]');
    var statusEl = document.getElementById('wizard-status');
    var queue = [];
    var current = 0;

    /* ── Step navigation ─────────────────────────────────────────────────── */
    function stepDone(i) {
        if (i === 0) return !!document.getElementById('title').value.trim();
        if (i === 1) return document.getElementById('cover_image').files.length > 0 || !!document.getElementById('cover-current-wrap');
        if (i === 2) return !!(document.getElementById('category_id').value || document.getElementById('tags').value.trim());
        return queue.length > 0 || !!panels[3].querySelector('.img-item:not(.img-item-pending)');
    }

    function refresh() {
        steps.forEach(function (s, n) { s.classList.toggle('is-done', stepDone(n)); });
    }

    function show(i) {
        current = Math.max(0, Math.min(i, panels.length - 1));
        panels.forEach(function (p, n) { p.classList.toggle('active', n === current); });
        steps.forEach(function (s, n) {
            s.classList.toggle('active', n === current);
            if (n === current) s.setAttribute('aria-current', 'step'); else s.removeAttribute('aria-current');
        });
        prevBtn.disabled = current === 0;
        nextBtn.hidden = current === panels.length - 1;
        if (wizard.getBoundingClientRect().top < 0) wizard.scrollIntoView({ behavior: 'smooth' });
        refresh();
    }

    steps.forEach(function (s, n) { s.addEventListener('click', function () { show(n); }); });
    prevBtn.addEventListener('click', function () { show(current - 1); });
    nextBtn.addEventListener('click', function () { show(current + 1); });
    form.addEventListener('input', refresh);
    form.addEventListener('change', refresh);

    // A required field inside a hidden step or language tab can't take focus,
    // so reveal the first invalid one before the browser reports it.
    var revealing = false;
    form.addEventListener('invalid', function (e) {
        if (revealing) return;
        revealing = true;
        setTimeout(function () { revealing = false; });
        var panel = e.target.closest('.wizard-panel');
        if (panel) show(panels.indexOf(panel));
        var lang = e.target.closest('.lang-panel');
        var tab = lang && wizard.querySelector('.lang-tab[data-target="' + lang.id + '"]');
        if (tab && !lang.classList.contains('active')) tab.click();
    }, true);

    function setStatus(text, type) {
        statusEl.className = 'ajax-flash' + (type ? ' ajax-flash-' + type : '');
        statusEl.textContent = text;
        statusEl.hidden = !text;
    }

    show(0);

    /* ── Create mode: gallery queue ──────────────────────────────────────── */
    var zone = document.getElementById('gallery-queue-zone');
    if (!zone || form.dataset.mode !== 'create') return;

    var grid = document.getElementById('gallery-queue-grid');
    var input = zone.querySelector('input[type="file"]');
    var MAX_BYTES = 5 * 1024 * 1024;
    var IMG_EXT = /\.(jpe?g|png|webp|gif)$/i;

    // Mirrors werkzeug's secure_filename(), which the server applies to the stored
    // name — so the @name shown here is the one the Markdown must reference.
    function secureName(name) {
        return name.normalize('NFKD').replace(/[^\x00-\x7f]/g, '')
            .split(/\s+/).filter(Boolean).join('_')
            .replace(/[^A-Za-z0-9_.-]/g, '').replace(/^[._]+|[._]+$/g, '');
    }

    function addFiles(files) {
        Array.prototype.forEach.call(files, function (file) {
            if (!IMG_EXT.test(file.name) || file.size > MAX_BYTES) {
                setStatus(msg.msgRejected.replace('{file}', file.name), 'error');
                return;
            }
            var item = document.createElement('div');
            item.className = 'img-item';
            var img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.alt = '';
            var del = document.createElement('button');
            del.type = 'button';
            del.className = 'del-img';
            del.title = msg.msgRemove;
            del.setAttribute('aria-label', msg.msgRemove + ' ' + file.name);
            del.textContent = '×';
            var name = document.createElement('code');
            name.className = 'img-item-name';
            name.textContent = '@' + secureName(file.name);
            name.title = name.textContent;
            item.append(img, del, name);

            var entry = { file: file };
            queue.push(entry);
            del.addEventListener('click', function () {
                queue.splice(queue.indexOf(entry), 1);
                URL.revokeObjectURL(img.src);
                item.remove();
                refresh();
            });
            grid.appendChild(item);
        });
        refresh();
    }

    zone.addEventListener('click', function (e) { if (e.target !== input) input.click(); });
    zone.addEventListener('dragover', function (e) { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', function (e) { if (!zone.contains(e.relatedTarget)) zone.classList.remove('drag-over'); });
    zone.addEventListener('drop', function (e) {
        e.preventDefault();
        zone.classList.remove('drag-over');
        addFiles(e.dataTransfer.files);
    });
    input.addEventListener('change', function () { addFiles(this.files); this.value = ''; });

    // Sequential so a slow connection doesn't fire N parallel 5 MB uploads. Never rejects.
    function uploadQueue(url) {
        var failed = [];
        return queue.reduce(function (chain, entry, i) {
            return chain.then(function () {
                setStatus(msg.msgUploading.replace('{i}', i + 1).replace('{n}', queue.length));
                var fd = new FormData();
                fd.append('image', entry.file);
                return fetch(url, { method: 'POST', body: fd, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                    .then(function (r) { if (!r.ok) throw new Error(); })
                    .catch(function () { failed.push(entry.file.name); });
            });
        }, Promise.resolve()).then(function () { return failed; });
    }

    // Step 1: create the post (without photos). Step 2: only if that passed, upload the gallery.
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        submitBtn.disabled = true;
        setStatus(msg.msgCreating);
        fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) {
                return r.json().catch(function () { return {}; }).then(function (data) {
                    if (!r.ok || !data.redirect) throw new Error(data.error || '');
                    return data;
                });
            })
            .then(function (data) {
                // From here the post exists: never re-enable submit, or a retry would create a duplicate.
                return uploadQueue(data.images_url).then(function (failed) {
                    if (!failed.length) { window.location.href = data.redirect; return; }
                    setStatus(msg.msgPartial.replace('{files}', failed.join(', ')) + ' ', 'error');
                    var link = document.createElement('a');
                    link.href = data.redirect;
                    link.textContent = msg.msgOpenPost;
                    statusEl.appendChild(link);
                });
            }, function (err) {
                submitBtn.disabled = false;
                setStatus((err.message ? err.message + ' ' : '') + msg.msgNotCreated, 'error');
            });
    });
}());
