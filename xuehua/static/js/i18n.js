// Xuehua - Shared language & i18n helpers
// Loaded before page-specific JS. Exposes window.XuehuaI18n.

var API = API || '';

const XuehuaI18n = {
    catalog: {},
    uiLanguage: 'zh',
    studyLanguage: 'ja',
    languages: [],
    uiLanguages: [],
    currentLevel: '',

    async init() {
        await this.loadLanguages();
        await this.loadI18n();
        this.populateLanguageSelects();
        this.applyTranslations();
        this.bindLanguageSelects();
    },

    async loadLanguages() {
        try {
            const resp = await fetch(`${API}/api/languages`);
            const data = await resp.json();
            this.languages = data.languages || [];
            this.uiLanguages = data.ui_languages || [];
            this.studyLanguage = data.current_language || 'ja';
            this.uiLanguage = data.current_ui_language || 'zh';
            this.currentLevel = data.current_level || '';
        } catch (e) {
            console.error('Failed to load languages:', e);
        }
    },

    async loadI18n() {
        try {
            const resp = await fetch(`${API}/api/i18n?ui=${encodeURIComponent(this.uiLanguage)}`);
            const data = await resp.json();
            this.catalog = data.catalog || {};
        } catch (e) {
            console.error('Failed to load i18n:', e);
        }
    },

    t(key, fallback) {
        return this.catalog[key] || fallback || key;
    },

    applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const text = this.catalog[key];
            if (text !== undefined) {
                el.textContent = text;
            }
        });
        document.documentElement.lang = this.uiLanguage === 'en' ? 'en' : 'zh';
    },

    getLanguageInfo(code) {
        return this.languages.find(l => l.code === code) || null;
    },

    populateLanguageSelects() {
        const langSelect = document.getElementById('select-language');
        if (langSelect) {
            langSelect.innerHTML = '';
            this.languages.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.code;
                opt.textContent = `${l.name_zh} / ${l.endonym}`;
                if (l.code === this.studyLanguage) opt.selected = true;
                langSelect.appendChild(opt);
            });
        }

        const uiSelect = document.getElementById('select-ui-language');
        if (uiSelect) {
            uiSelect.innerHTML = '';
            this.uiLanguages.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.code;
                opt.textContent = l.endonym || l.name_en || l.code;
                if (l.code === this.uiLanguage) opt.selected = true;
                uiSelect.appendChild(opt);
            });
        }

        this.populateLevelSelect();
    },

    populateLevelSelect() {
        const levelSelect = document.getElementById('select-level');
        if (!levelSelect) return;
        const info = this.getLanguageInfo(this.studyLanguage);
        levelSelect.innerHTML = '';
        if (!info) return;

        if (!info.levels || info.levels.length === 0) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = this.t('learn.all_levels', '全部');
            levelSelect.appendChild(opt);
            return;
        }

        info.levels.forEach(lv => {
            const opt = document.createElement('option');
            opt.value = lv;
            opt.textContent = (info.level_labels && info.level_labels[lv]) || lv;
            if (lv === this.currentLevel) opt.selected = true;
            levelSelect.appendChild(opt);
        });

        // "All levels" option
        const allOpt = document.createElement('option');
        allOpt.value = '';
        allOpt.textContent = this.t('learn.all_levels', '全部');
        levelSelect.appendChild(allOpt);
    },

    bindLanguageSelects() {
        const langSelect = document.getElementById('select-language');
        if (langSelect) {
            langSelect.addEventListener('change', async () => {
                this.studyLanguage = langSelect.value;
                const info = this.getLanguageInfo(this.studyLanguage);
                this.currentLevel = info ? (info.default_level || (info.levels[0] || '')) : '';
                await this.setLanguage({ language: this.studyLanguage, level: this.currentLevel });
                this.populateLevelSelect();
                this.updateFuriganaVisibility(info);
                this.notifyLanguageChange();
            });
        }

        const uiSelect = document.getElementById('select-ui-language');
        if (uiSelect) {
            uiSelect.addEventListener('change', async () => {
                this.uiLanguage = uiSelect.value;
                await this.setLanguage({ ui_language: this.uiLanguage });
                await this.loadI18n();
                this.applyTranslations();
            });
        }

        const levelSelect = document.getElementById('select-level');
        if (levelSelect) {
            levelSelect.addEventListener('change', async () => {
                this.currentLevel = levelSelect.value;
                await this.setLanguage({ level: this.currentLevel });
                this.notifyLanguageChange();
            });
        }
    },

    updateFuriganaVisibility(info) {
        if (!info) return;
        // Hide furigana/romaji toggles for languages that don't support them
        const furiganaToggle = document.getElementById('toggle-furigana');
        const romajiToggle = document.getElementById('toggle-romaji');
        if (furiganaToggle) furiganaToggle.parentElement.style.display = info.has_furigana ? '' : 'none';
        if (romajiToggle) romajiToggle.parentElement.style.display = info.has_romaji ? '' : 'none';
    },

    async setLanguage(payload) {
        try {
            await fetch(`${API}/api/language/set`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
        } catch (e) {
            console.error('Failed to set language:', e);
        }
    },

    notifyLanguageChange() {
        document.dispatchEvent(new CustomEvent('xuehua:language-changed', {
            detail: {
                language: this.studyLanguage,
                level: this.currentLevel,
                uiLanguage: this.uiLanguage,
            },
        }));
    },
};

document.addEventListener('DOMContentLoaded', () => {
    XuehuaI18n.init();
});