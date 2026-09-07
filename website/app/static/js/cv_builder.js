/* ══════════════════════════════════════════════════════════════════════════
   CV Builder — structured form that assembles a RenderCV-shaped JSON blob,
   which the server (app/services/rendercv_service.py) turns into YAML and
   renders to a PDF via the real `rendercv` CLI.

   Only loaded on admin/cv/form.html. Field defs here must stay in sync with
   BUILDER_ENTRY_TYPES in rendercv_service.py (and, underneath that, with
   rendercv's own entry models under rendercv/schema/models/cv/entries/) —
   this is intentional, documented duplication: this file drives per-field
   labels/required-flags/textarea-vs-input rendering that has no server-side
   equivalent to read from.
   ══════════════════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    var panel = document.getElementById('panel-source-builder');
    if (!panel) return;

    /* ── Entry type field definitions ────────────────────────────────────── */
    var ENTRY_FIELD_DEFS = {
        education: [
            { key: 'institution', label: 'Institution', required: true },
            { key: 'area', label: 'Area / field of study', required: true },
            { key: 'degree', label: 'Degree', placeholder: 'BS, MS, PhD…' },
            { key: 'date', label: 'Date (if a single date, leave start/end blank)' },
            { key: 'start_date', label: 'Start date', placeholder: 'YYYY-MM' },
            { key: 'end_date', label: 'End date', placeholder: 'YYYY-MM or "present"' },
            { key: 'location', label: 'Location' },
            { key: 'summary', label: 'Summary', textarea: true },
            { key: 'highlights', label: 'Highlights (one per line)', textarea: true, list: true },
        ],
        experience: [
            { key: 'company', label: 'Company', required: true },
            { key: 'position', label: 'Position', required: true },
            { key: 'date', label: 'Date (if a single date, leave start/end blank)' },
            { key: 'start_date', label: 'Start date', placeholder: 'YYYY-MM' },
            { key: 'end_date', label: 'End date', placeholder: 'YYYY-MM or "present"' },
            { key: 'location', label: 'Location' },
            { key: 'summary', label: 'Summary', textarea: true },
            { key: 'highlights', label: 'Highlights (one per line)', textarea: true, list: true },
        ],
        normal: [
            { key: 'name', label: 'Name', required: true, placeholder: 'Project / award / certification name' },
            { key: 'date', label: 'Date (if a single date, leave start/end blank)' },
            { key: 'start_date', label: 'Start date', placeholder: 'YYYY-MM' },
            { key: 'end_date', label: 'End date', placeholder: 'YYYY-MM or "present"' },
            { key: 'location', label: 'Location' },
            { key: 'summary', label: 'Summary', textarea: true },
            { key: 'highlights', label: 'Highlights (one per line)', textarea: true, list: true },
        ],
        one_line: [
            { key: 'label', label: 'Label', required: true, placeholder: 'Languages, Citizenship…' },
            { key: 'details', label: 'Details', required: true, placeholder: 'English (native), Spanish (fluent)' },
        ],
        publication: [
            { key: 'title', label: 'Title', required: true },
            { key: 'authors', label: 'Authors (one per line)', textarea: true, list: true, required: true },
            { key: 'summary', label: 'Summary', textarea: true },
            { key: 'doi', label: 'DOI' },
            { key: 'url', label: 'URL' },
            { key: 'journal', label: 'Journal / venue' },
            { key: 'date', label: 'Date', placeholder: 'YYYY-MM' },
        ],
        bullet: [
            { key: 'bullet', label: 'Text', required: true },
        ],
        numbered: [
            { key: 'number', label: 'Text', required: true },
        ],
        reversed_numbered: [
            { key: 'reversed_number', label: 'Text', required: true },
        ],
    };

    var ENTRY_TYPE_LABELS = {
        education: 'Education',
        experience: 'Experience',
        normal: 'Project / Award / Other',
        one_line: 'Skill (one line)',
        publication: 'Publication',
        bullet: 'Bullet point',
        numbered: 'Numbered item',
        reversed_numbered: 'Reversed-numbered item',
        text: 'Plain text (paragraphs)',
    };
    var SECTION_TYPE_OPTIONS = Object.keys(ENTRY_FIELD_DEFS).concat(['text']);

    var nextId = 1;
    function genId() { return nextId++; }

    var CONSTANTS = { themes: [], social_networks: [] };
    function readConstants() {
        var el = document.getElementById('cv-builder-constants');
        if (!el) return;
        try {
            var parsed = JSON.parse(el.textContent || '{}');
            CONSTANTS.themes = parsed.themes || [];
            CONSTANTS.social_networks = parsed.social_networks || [];
        } catch (e) { /* keep defaults */ }
    }

    function createEmptyState() {
        return {
            header: { name: '', headline: '', location: '', email: '', phone: '', website: '' },
            social_networks: [],
            sections: [],
            design: { theme: 'classic' },
        };
    }

    var state = createEmptyState();

    function hydrateFromInitialData() {
        var el = document.getElementById('cv-builder-initial-data');
        var data = null;
        if (el) {
            try { data = JSON.parse(el.textContent || 'null'); } catch (e) { data = null; }
        }
        if (!data || typeof data !== 'object') return createEmptyState();

        var fresh = createEmptyState();
        fresh.header = Object.assign({}, fresh.header, data.header || {});
        fresh.design = Object.assign({}, fresh.design, data.design || {});
        fresh.social_networks = (data.social_networks || []).map(function (sn) {
            return { id: genId(), network: sn.network || CONSTANTS.social_networks[0] || '', username: sn.username || '' };
        });
        fresh.sections = (data.sections || []).map(function (sec) {
            return {
                id: genId(),
                title: sec.title || '',
                entry_type: sec.entry_type || 'normal',
                text: sec.text || '',
                entries: (sec.entries || []).map(function (entry) {
                    return { id: genId(), fields: Object.assign({}, entry.fields || {}) };
                }),
            };
        });
        return fresh;
    }

    /* ── Header + theme ───────────────────────────────────────────────────── */
    function bindHeaderFields() {
        var map = {
            builder_name: 'name', builder_headline: 'headline', builder_location: 'location',
            builder_email: 'email', builder_phone: 'phone', builder_website: 'website',
        };
        Object.keys(map).forEach(function (inputId) {
            var input = document.getElementById(inputId);
            if (!input) return;
            var key = map[inputId];
            input.value = state.header[key] || '';
            input.addEventListener('input', function () { state.header[key] = this.value; });
        });
    }

    function bindThemeSelect() {
        var select = document.getElementById('builder_theme');
        if (!select) return;
        if (state.design.theme && select.querySelector('option[value="' + state.design.theme + '"]')) {
            select.value = state.design.theme;
        } else if (select.options.length) {
            state.design.theme = select.value;
        }
        select.addEventListener('change', function () { state.design.theme = this.value; });
    }

    /* ── Social networks ──────────────────────────────────────────────────── */
    function renderSocialNetworks() {
        var list = document.getElementById('social-networks-list');
        list.innerHTML = '';
        if (!state.social_networks.length) {
            var hint = document.createElement('p');
            hint.className = 'form-hint';
            hint.textContent = 'No social networks yet.';
            list.appendChild(hint);
            return;
        }
        state.social_networks.forEach(function (sn) { list.appendChild(renderSocialNetworkRow(sn)); });
    }

    function renderSocialNetworkRow(sn) {
        var row = document.createElement('div');
        row.className = 'builder-row';

        var select = document.createElement('select');
        CONSTANTS.social_networks.forEach(function (name) {
            var opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            if (name === sn.network) opt.selected = true;
            select.appendChild(opt);
        });
        if (!sn.network && CONSTANTS.social_networks.length) sn.network = CONSTANTS.social_networks[0];
        select.addEventListener('change', function () { sn.network = this.value; });

        var input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'username';
        input.value = sn.username || '';
        input.addEventListener('input', function () { sn.username = this.value; });

        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-danger btn-sm';
        removeBtn.textContent = '×';
        removeBtn.addEventListener('click', function () { removeSocialNetwork(sn.id); });

        row.appendChild(select);
        row.appendChild(input);
        row.appendChild(removeBtn);
        return row;
    }

    function addSocialNetwork() {
        state.social_networks.push({ id: genId(), network: CONSTANTS.social_networks[0] || '', username: '' });
        renderSocialNetworks();
    }

    function removeSocialNetwork(id) {
        state.social_networks = state.social_networks.filter(function (sn) { return sn.id !== id; });
        renderSocialNetworks();
    }

    /* ── Sections + entries ───────────────────────────────────────────────── */
    function renderSections() {
        var list = document.getElementById('sections-list');
        list.innerHTML = '';
        if (!state.sections.length) {
            var hint = document.createElement('p');
            hint.className = 'form-hint';
            hint.textContent = 'No sections yet — add one below.';
            list.appendChild(hint);
            return;
        }
        state.sections.forEach(function (section) { list.appendChild(renderSectionCard(section)); });
    }

    function renderSectionCard(section) {
        var card = document.createElement('div');
        card.className = 'section-card';

        var header = document.createElement('div');
        header.className = 'section-card-header';

        var titleGroup = document.createElement('div');
        titleGroup.className = 'form-group';
        var titleLabel = document.createElement('label');
        titleLabel.textContent = 'Section title';
        var titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.placeholder = 'Experience, Education, Skills…';
        titleInput.value = section.title || '';
        titleInput.addEventListener('input', function () { section.title = this.value; });
        titleGroup.appendChild(titleLabel);
        titleGroup.appendChild(titleInput);

        var typeGroup = document.createElement('div');
        typeGroup.className = 'form-group';
        var typeLabel = document.createElement('label');
        typeLabel.textContent = 'Entry type';
        var typeSelect = document.createElement('select');
        SECTION_TYPE_OPTIONS.forEach(function (type) {
            var opt = document.createElement('option');
            opt.value = type;
            opt.textContent = ENTRY_TYPE_LABELS[type] || type;
            if (type === section.entry_type) opt.selected = true;
            typeSelect.appendChild(opt);
        });
        typeSelect.addEventListener('change', function () {
            var hasContent = section.entries.length > 0 || (section.text || '').trim();
            if (hasContent && !confirm('Change entry type? Existing entries in this section will be cleared.')) {
                typeSelect.value = section.entry_type;
                return;
            }
            section.entry_type = this.value;
            section.entries = [];
            section.text = '';
            renderEntriesForSection(section);
            addEntryBtnVisibility(section);
        });
        typeGroup.appendChild(typeLabel);
        typeGroup.appendChild(typeSelect);

        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-danger btn-sm';
        removeBtn.textContent = 'Remove section';
        removeBtn.addEventListener('click', function () { removeSection(section.id); });

        header.appendChild(titleGroup);
        header.appendChild(typeGroup);
        header.appendChild(removeBtn);
        card.appendChild(header);

        var entriesContainer = document.createElement('div');
        entriesContainer.className = 'section-entries';
        card.appendChild(entriesContainer);

        var addEntryBtn = document.createElement('button');
        addEntryBtn.type = 'button';
        addEntryBtn.className = 'btn btn-ghost btn-sm';
        addEntryBtn.textContent = '+ Add entry';
        addEntryBtn.addEventListener('click', function () { addEntry(section.id); });
        card.appendChild(addEntryBtn);

        section._entriesContainer = entriesContainer;
        section._addEntryBtn = addEntryBtn;
        renderEntriesForSection(section);
        addEntryBtnVisibility(section);

        return card;
    }

    function addEntryBtnVisibility(section) {
        if (section._addEntryBtn) {
            section._addEntryBtn.style.display = section.entry_type === 'text' ? 'none' : '';
        }
    }

    function renderEntriesForSection(section) {
        var container = section._entriesContainer;
        if (!container) return;
        container.innerHTML = '';

        if (section.entry_type === 'text') {
            var textarea = document.createElement('textarea');
            textarea.rows = 4;
            textarea.placeholder = 'One paragraph per line…';
            textarea.value = section.text || '';
            textarea.addEventListener('input', function () { section.text = this.value; });
            container.appendChild(textarea);
            return;
        }

        section.entries.forEach(function (entry) { container.appendChild(renderEntry(section, entry)); });
    }

    function renderEntry(section, entry) {
        var defs = ENTRY_FIELD_DEFS[section.entry_type] || [];
        var card = document.createElement('div');
        card.className = 'entry-card';

        var fieldsWrap = document.createElement('div');
        fieldsWrap.className = 'entry-card-fields';

        defs.forEach(function (def) {
            var group = document.createElement('div');
            group.className = 'form-group';

            var label = document.createElement('label');
            label.textContent = def.label + (def.required ? ' *' : '');
            group.appendChild(label);

            var input = def.textarea ? document.createElement('textarea') : document.createElement('input');
            if (!def.textarea) input.type = 'text';
            else input.rows = def.list ? 3 : 2;
            if (def.placeholder) input.placeholder = def.placeholder;
            input.value = entry.fields[def.key] || '';
            input.addEventListener('input', function () { entry.fields[def.key] = this.value; });
            group.appendChild(input);

            fieldsWrap.appendChild(group);
        });

        card.appendChild(fieldsWrap);

        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-danger btn-sm';
        removeBtn.style.marginTop = '8px';
        removeBtn.textContent = 'Remove entry';
        removeBtn.addEventListener('click', function () { removeEntry(section.id, entry.id); });
        card.appendChild(removeBtn);

        return card;
    }

    function addSection() {
        state.sections.push({ id: genId(), title: '', entry_type: 'normal', entries: [], text: '' });
        renderSections();
    }

    function removeSection(id) {
        state.sections = state.sections.filter(function (s) { return s.id !== id; });
        renderSections();
    }

    function addEntry(sectionId) {
        var section = state.sections.filter(function (s) { return s.id === sectionId; })[0];
        if (!section) return;
        section.entries.push({ id: genId(), fields: {} });
        renderEntriesForSection(section);
    }

    function removeEntry(sectionId, entryId) {
        var section = state.sections.filter(function (s) { return s.id === sectionId; })[0];
        if (!section) return;
        section.entries = section.entries.filter(function (e) { return e.id !== entryId; });
        renderEntriesForSection(section);
    }

    /* ── Init ─────────────────────────────────────────────────────────────── */
    function init() {
        readConstants();
        state = hydrateFromInitialData();

        bindHeaderFields();
        bindThemeSelect();
        renderSocialNetworks();
        renderSections();

        var addSnBtn = document.getElementById('add-social-network-btn');
        if (addSnBtn) addSnBtn.addEventListener('click', addSocialNetwork);

        var addSecBtn = document.getElementById('add-section-btn');
        if (addSecBtn) addSecBtn.addEventListener('click', addSection);

        var form = panel.closest('form');
        var jsonField = document.getElementById('cv_builder_json_field');
        if (form && jsonField) {
            form.addEventListener('submit', function () {
                var payload = {
                    header: state.header,
                    social_networks: state.social_networks.map(function (sn) {
                        return { network: sn.network, username: sn.username };
                    }),
                    sections: state.sections.map(function (sec) {
                        return {
                            title: sec.title,
                            entry_type: sec.entry_type,
                            text: sec.text,
                            entries: sec.entries.map(function (e) { return { fields: e.fields }; }),
                        };
                    }),
                    design: state.design,
                };
                jsonField.value = JSON.stringify(payload);
            });
        }
    }

    if (document.readyState !== 'loading') init();
    else document.addEventListener('DOMContentLoaded', init);
}());
