/* ══════════════════════════════════════════════════════════════════════════
   Admin panel — shared behaviors
   Loaded once on every admin page (see admin/base.html). Each init function
   guards on the presence of its target elements, so it's safe to include
   everywhere rather than duplicating this logic per-template.
   ══════════════════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }

    /* ── Language tabs (EN/ES, or CV's Upload-vs-Generate mode) ──────────── */
    function initLangTabs() {
        var tabs = document.querySelectorAll('.lang-tab');
        if (!tabs.length) return;
        tabs.forEach(function (tab) {
            tab.addEventListener('click', function () {
                document.querySelectorAll('.lang-tab').forEach(function (t) { t.classList.remove('active'); });
                document.querySelectorAll('.lang-panel').forEach(function (p) { p.classList.remove('active'); });
                this.classList.add('active');
                var targetId = this.dataset.target;
                var panel = document.getElementById(targetId);
                if (panel) panel.classList.add('active');
                document.dispatchEvent(new CustomEvent('admin:langtab', { detail: { target: targetId, tab: this } }));
            });
        });
    }

    /* ── Spanish enable/disable toggle ────────────────────────────────────── */
    function initEsToggle() {
        var enableEs = document.getElementById('enable_es');
        var esFields = document.getElementById('es-fields');
        if (!enableEs || !esFields) return;
        function sync() { esFields.classList.toggle('disabled', !enableEs.checked); }
        enableEs.addEventListener('change', sync);
        sync();
    }

    /* ── Single-image FileReader preview (cover/photo uploads) ───────────── */
    function initImagePreview() {
        ['cover_image', 'image'].forEach(function (inputId) {
            var input = document.getElementById(inputId);
            var previewWrap = document.getElementById('cover-preview-wrap');
            var previewImg = document.getElementById('cover-preview-img');
            var currentWrap = document.getElementById('cover-current-wrap');
            if (!input || !previewWrap || !previewImg) return;
            input.addEventListener('change', function () {
                var file = this.files[0];
                if (!file) return;
                var reader = new FileReader();
                reader.onload = function (e) {
                    previewImg.src = e.target.result;
                    previewWrap.style.display = 'flex';
                    if (currentWrap) currentWrap.style.display = 'none';
                };
                reader.readAsDataURL(file);
            });
        });
    }

    /* ── Auto-slug from title (create mode only — slug is readonly on edit) ── */
    function initAutoSlug() {
        var titleInput = document.getElementById('title');
        var slugInput = document.getElementById('slug');
        if (!titleInput || !slugInput || slugInput.readOnly) return;
        var manuallyEdited = false;
        slugInput.addEventListener('input', function () { manuallyEdited = !!this.value; });
        titleInput.addEventListener('input', function () {
            if (manuallyEdited) return;
            slugInput.value = this.value.toLowerCase().trim()
                .replace(/[^\w\s-]/g, '').replace(/[\s_]+/g, '-')
                .replace(/-{2,}/g, '-').replace(/^-+|-+$/g, '');
        });
    }

    /* ── Publish toggle (AJAX fetch, URL supplied per-element) ────────────── */
    function initPublishToggle() {
        document.querySelectorAll('.publish-toggle[data-toggle-url]').forEach(function (toggle) {
            toggle.addEventListener('click', function () {
                var url = toggle.dataset.toggleUrl;
                toggle.disabled = true;
                fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.error) { toggle.disabled = false; return; }
                        toggle.classList.toggle('is-published', !!data.published);
                        toggle.title = data.published ? 'Click to unpublish' : 'Click to publish';
                        var label = toggle.querySelector('.toggle-label');
                        if (label) label.textContent = data.published ? 'Published' : 'Draft';
                        toggle.disabled = false;
                        document.dispatchEvent(new CustomEvent('admin:publishtoggle', {
                            detail: { published: data.published, toggle: toggle }
                        }));
                    })
                    .catch(function () { toggle.disabled = false; });
            });
        });
    }

    /* ── Bulk select + bulk delete ─────────────────────────────────────────── */
    function initBulkSelect() {
        var bulkForm = document.getElementById('bulk-form');
        var selectAll = document.getElementById('select-all');
        var bulkBtn = document.getElementById('bulk-delete-btn');
        var countLabel = document.getElementById('selected-count');
        if (!bulkForm || !selectAll || !bulkBtn || !countLabel) return;

        function rowCheckboxes() {
            return Array.prototype.slice.call(bulkForm.querySelectorAll('.row-checkbox'));
        }
        function updateState() {
            var checked = rowCheckboxes().filter(function (cb) { return cb.checked; });
            countLabel.textContent = checked.length;
            bulkBtn.disabled = checked.length === 0;
            selectAll.checked = checked.length > 0 && checked.length === rowCheckboxes().length;
            selectAll.indeterminate = checked.length > 0 && checked.length < rowCheckboxes().length;
        }
        selectAll.addEventListener('change', function () {
            rowCheckboxes().forEach(function (cb) { cb.checked = selectAll.checked; });
            updateState();
        });
        bulkForm.addEventListener('change', function (e) {
            if (e.target.classList.contains('row-checkbox')) updateState();
        });
        bulkBtn.addEventListener('click', function (e) {
            var count = rowCheckboxes().filter(function (cb) { return cb.checked; }).length;
            if (!confirm('Delete ' + count + ' selected item(s)?')) e.preventDefault();
        });
        updateState();
    }

    /* ── Image manager: drag-drop multi-upload + AJAX delete + copy-URL ────── */
    function showFlash(msg, type) {
        var container = document.getElementById('ajax-flash-container');
        if (!container) return;
        var d = document.createElement('div');
        d.className = 'ajax-flash ajax-flash-' + type;
        d.textContent = msg;
        container.appendChild(d);
        setTimeout(function () { d.remove(); }, 5000);
    }

    function flashCopied(btn) {
        var orig = btn.textContent;
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(function () { btn.textContent = orig; btn.classList.remove('copied'); }, 1800);
    }

    function handleCopy(e) {
        var btn = e.currentTarget;
        var url = btn.dataset.url;
        if (!navigator.clipboard) {
            var ta = document.createElement('textarea');
            ta.value = url; ta.style.position = 'fixed'; ta.style.opacity = '0';
            document.body.appendChild(ta); ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            flashCopied(btn);
            return;
        }
        navigator.clipboard.writeText(url).then(function () { flashCopied(btn); });
    }

    window.AdminImg = window.AdminImg || {};
    window.AdminImg.delete = function (url, card) {
        card.style.opacity = '0.35';
        card.style.pointerEvents = 'none';
        fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.ok) { card.remove(); }
                else { card.style.opacity = '1'; card.style.pointerEvents = ''; showFlash('Failed to remove image.', 'error'); }
            })
            .catch(function () { card.style.opacity = '1'; card.style.pointerEvents = ''; showFlash('Failed to remove image.', 'error'); });
    };

    function initImageManager() {
        document.querySelectorAll('.upload-zone[data-upload-url]').forEach(function (zone) {
            var uploadUrl = zone.dataset.uploadUrl;
            var card = zone.closest('.card');
            var grid = card ? card.querySelector('.img-grid') : null;
            var fileInput = zone.querySelector('input[type="file"]');
            if (!grid || !fileInput) return;

            zone.addEventListener('click', function (e) { if (e.target !== fileInput) fileInput.click(); });
            zone.addEventListener('dragover', function (e) { e.preventDefault(); zone.classList.add('drag-over'); });
            zone.addEventListener('dragleave', function (e) { if (!zone.contains(e.relatedTarget)) zone.classList.remove('drag-over'); });
            zone.addEventListener('drop', function (e) {
                e.preventDefault(); zone.classList.remove('drag-over');
                for (var i = 0; i < e.dataTransfer.files.length; i++) upload(e.dataTransfer.files[i]);
            });
            fileInput.addEventListener('change', function () {
                for (var i = 0; i < this.files.length; i++) upload(this.files[i]);
                this.value = '';
            });

            function upload(file) {
                var hint = document.getElementById('no-images-hint');
                if (hint) hint.remove();

                var pending = document.createElement('div');
                pending.className = 'img-item img-item-pending';
                pending.innerHTML = '<div class="img-spinner"></div>';
                grid.appendChild(pending);

                var fd = new FormData();
                fd.append('image', file);
                fetch(uploadUrl, { method: 'POST', body: fd, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.error) { pending.remove(); showFlash(data.error, 'error'); }
                        else { pending.replaceWith(buildCard(data.id, data.url)); }
                    })
                    .catch(function () { pending.remove(); showFlash('Upload failed — please try again.', 'error'); });
            }

            function buildCard(id, url) {
                var deleteUrl = uploadUrl + '/' + id + '/delete';
                var div = document.createElement('div');
                div.className = 'img-item';
                div.id = 'img-' + id;
                div.innerHTML =
                    '<img src="' + url + '" alt="Image ' + id + '">' +
                    '<div class="blog-img-actions">' +
                    '<button type="button" class="copy-url-btn" data-url="' + url + '" title="Copy URL to clipboard">Copy URL</button>' +
                    '<button type="button" class="del-img" title="Remove">×</button>' +
                    '</div>';
                div.querySelector('.copy-url-btn').addEventListener('click', handleCopy);
                div.querySelector('.del-img').addEventListener('click', function () {
                    window.AdminImg.delete(deleteUrl, div);
                });
                return div;
            }
        });

        // Wire up copy/delete buttons already rendered server-side
        document.querySelectorAll('.copy-url-btn').forEach(function (btn) {
            btn.addEventListener('click', handleCopy);
        });
        document.querySelectorAll('.del-img[data-delete-url]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                window.AdminImg.delete(btn.dataset.deleteUrl, btn.closest('.img-item'));
            });
        });
    }

    ready(function () {
        initLangTabs();
        initEsToggle();
        initImagePreview();
        initAutoSlug();
        initPublishToggle();
        initBulkSelect();
        initImageManager();
    });
}());
