/* blog_ai.js — "Generate with AI" buttons on the blog post form (EN excerpt+tags, ES excerpt).
   Loaded only when ai_enabled is true (see post_form.html). */
(function () {
    'use strict';

    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }

    function mergeTags(currentValue, suggested) {
        var seen = {};
        var tags = [];
        currentValue.split(',').forEach(function (raw) {
            var name = raw.trim();
            if (!name) return;
            var key = name.toLowerCase();
            if (seen[key]) return;
            seen[key] = true;
            tags.push(name);
        });
        suggested.forEach(function (name) {
            name = (name || '').trim();
            if (!name) return;
            var key = name.toLowerCase();
            if (seen[key]) return;
            seen[key] = true;
            tags.push(name);
        });
        return tags.join(', ');
    }

    function wireButton(btn) {
        var titleInput = document.getElementById(btn.dataset.titleInput);
        var titleFallback = btn.dataset.titleFallbackInput ? document.getElementById(btn.dataset.titleFallbackInput) : null;
        var mdInput = document.getElementById(btn.dataset.markdownInput);
        var descInput = document.getElementById(btn.dataset.descriptionInput);
        var tagsInput = btn.dataset.tagsInput ? document.getElementById(btn.dataset.tagsInput) : null;
        var errorEl = document.getElementById(btn.dataset.errorTarget);
        if (!titleInput || !mdInput || !descInput || !errorEl) return;

        btn.addEventListener('click', function () {
            var title = titleInput.value.trim();
            if (!title && titleFallback) title = titleFallback.value.trim();
            errorEl.style.display = 'none';

            if (!title) {
                errorEl.textContent = errorEl.dataset.titleRequired || 'Add a title first.';
                errorEl.style.display = '';
                return;
            }

            var fd = new FormData();
            fd.append('title', title);
            fd.append('language', btn.dataset.language || 'en');
            if (mdInput.files && mdInput.files[0]) {
                fd.append('markdown_file', mdInput.files[0]);
            } else if (btn.dataset.postId) {
                fd.append('post_id', btn.dataset.postId);
            }

            btn.disabled = true;
            btn.textContent = btn.dataset.labelBusy || 'Generating…';

            fetch(btn.dataset.url, { method: 'POST', body: fd, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
                .then(function (result) {
                    if (!result.ok || result.data.error) {
                        errorEl.textContent = result.data.error || 'AI request failed.';
                        errorEl.style.display = '';
                        return;
                    }
                    descInput.value = result.data.description || descInput.value;
                    if (tagsInput && Array.isArray(result.data.tags) && result.data.tags.length) {
                        tagsInput.value = mergeTags(tagsInput.value, result.data.tags);
                    }
                })
                .catch(function () {
                    errorEl.textContent = 'AI request failed — check your connection and try again.';
                    errorEl.style.display = '';
                })
                .finally(function () {
                    btn.disabled = false;
                    btn.textContent = btn.dataset.label || 'Generate with AI';
                });
        });
    }

    function initAiSuggest() {
        document.querySelectorAll('.ai-suggest-btn').forEach(wireButton);
    }

    ready(initAiSuggest);
}());
