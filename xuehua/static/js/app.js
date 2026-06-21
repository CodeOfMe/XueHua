// Xuehua - Main Application JavaScript
var API = API || '';

class XuehuaApp {
    constructor() {
        this.settings = {
            showFurigana: true,
            showRomaji: false,
            currentLevel: 'N5',
            chatModel: '',
            embedModel: '',
        };
        this.models = { chatModels: [], embedModels: [] };
        this.collections = [];
        this.init();
    }

    async init() {
        await this.loadSettings();
        await this.loadModels();
        this.bindEvents();
        this.loadProgress();
        this.loadCollections();
    }

    async loadSettings() {
        try {
            const resp = await fetch(`${API}/api/settings`);
            const data = await resp.json();
            this.settings = { ...this.settings, ...data };
            this.applySettings();
        } catch (e) {
            console.error('Failed to load settings:', e);
        }
    }

    applySettings() {
        const toggleFurigana = document.getElementById('toggle-furigana');
        const toggleRomaji = document.getElementById('toggle-romaji');
        const selectLevel = document.getElementById('select-level');

        if (toggleFurigana) toggleFurigana.checked = this.settings.showFurigana;
        if (toggleRomaji) toggleRomaji.checked = this.settings.showRomaji;
        if (selectLevel) selectLevel.value = this.settings.currentLevel || 'N5';
    }

    async loadModels() {
        try {
            const resp = await fetch(`${API}/api/models`);
            const data = await resp.json();
            this.models = data;

            const chatSelect = document.getElementById('select-chat-model');
            if (chatSelect) {
                chatSelect.innerHTML = '';
                if (data.chatModels && data.chatModels.length > 0) {
                    data.chatModels.forEach(m => {
                        const opt = document.createElement('option');
                        opt.value = m;
                        opt.textContent = m;
                        if (m === data.currentChat) opt.selected = true;
                        chatSelect.appendChild(opt);
                    });
                } else {
                    const opt = document.createElement('option');
                    opt.value = '';
                    opt.textContent = '无可用的模型';
                    chatSelect.appendChild(opt);
                }
            }

            const embedSelect = document.getElementById('settings-embed-model');
            if (embedSelect) {
                embedSelect.innerHTML = '';
                if (data.embedModels && data.embedModels.length > 0) {
                    data.embedModels.forEach(m => {
                        const opt = document.createElement('option');
                        opt.value = m;
                        opt.textContent = m;
                        if (m === data.currentEmbed) opt.selected = true;
                        embedSelect.appendChild(opt);
                    });
                }
            }
        } catch (e) {
            console.error('Failed to load models:', e);
        }
    }

    async loadProgress() {
        try {
            const [progressResp, srsResp] = await Promise.all([
                fetch(`${API}/api/learning/progress`),
                fetch(`${API}/api/learning/srs/stats`),
            ]);
            const progress = await progressResp.json();
            const srs = await srsResp.json();

            if (progress.success) {
                const data = progress.data;
                const el = id => document.getElementById(id);
                if (el('progress-level')) el('progress-level').textContent = data.current_level || 'N5';
                if (el('progress-vocab')) el('progress-vocab').textContent = data.vocabulary_count || 0;
                if (el('progress-kanji')) el('progress-kanji').textContent = data.kanji_count || 0;
                if (el('progress-due')) el('progress-due').textContent = srs.data ? srs.data.due : 0;
            }
        } catch (e) {
            console.error('Failed to load progress:', e);
        }
    }

    async loadCollections() {
        try {
            const resp = await fetch(`${API}/api/kb/collections`);
            const data = await resp.json();
            this.collections = data.collections || [];

            const container = document.getElementById('kb-collections');
            if (container) {
                if (this.collections.length === 0) {
                    container.innerHTML = '<div class="status-text">尚无知识库</div>';
                } else {
                    container.innerHTML = this.collections.map(c =>
                        `<div class="kb-item"><span class="kb-item-name">${c.name}</span><span class="kb-item-count">${c.count} 条</span></div>`
                    ).join('');
                }
            }

            const statusEl = document.getElementById('kb-status');
            if (statusEl) {
                const total = this.collections.reduce((sum, c) => sum + c.count, 0);
                statusEl.textContent = `${this.collections.length} 个知识库，共 ${total} 条`;
            }
        } catch (e) {
            console.error('Failed to load collections:', e);
        }
    }

    bindEvents() {
        const toggleFurigana = document.getElementById('toggle-furigana');
        const toggleRomaji = document.getElementById('toggle-romaji');
        const selectLevel = document.getElementById('select-level');
        const selectChatModel = document.getElementById('select-chat-model');
        const btnBuildKB = document.getElementById('btn-build-kb');
        const btnSettings = document.getElementById('btn-settings');
        const btnSaveSettings = document.getElementById('btn-save-settings');
        const btnCloseSettings = document.getElementById('btn-close-settings');
        const btnStartBuild = document.getElementById('btn-start-build');
        const btnCloseBuild = document.getElementById('btn-close-build');
        const btnBrowseDir = document.getElementById('btn-browse-dir');
        const btnDirUp = document.getElementById('btn-dir-up');
        const btnDirSelect = document.getElementById('btn-dir-select');
        const btnDirCancel = document.getElementById('btn-dir-cancel');

        if (toggleFurigana) {
            toggleFurigana.addEventListener('change', () => {
                this.settings.showFurigana = toggleFurigana.checked;
                this.saveSettings();
            });
        }

        if (toggleRomaji) {
            toggleRomaji.addEventListener('change', () => {
                this.settings.showRomaji = toggleRomaji.checked;
                this.saveSettings();
            });
        }

        if (selectLevel) {
            selectLevel.addEventListener('change', () => {
                this.settings.currentLevel = selectLevel.value;
                // i18n.js handles saving + API call for level changes
                if (!window.XuehuaI18n) {
                    this.saveSettings();
                    fetch(`${API}/api/learning/progress`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ current_level: selectLevel.value }),
                    });
                }
            });
        }

        if (selectChatModel) {
            selectChatModel.addEventListener('change', () => {
                this.settings.chatModel = selectChatModel.value;
                this.saveSettings();
            });
        }

        if (btnBuildKB) {
            btnBuildKB.addEventListener('click', () => {
                const epubInput = document.getElementById('build-epub-dir');
                if (epubInput && !epubInput.value && this.settings.epub_dir) {
                    epubInput.value = this.settings.epub_dir;
                }
                document.getElementById('build-modal').classList.remove('hidden');
            });
        }

        if (btnSettings) {
            btnSettings.addEventListener('click', () => {
                const modal = document.getElementById('settings-modal');
                const urlInput = document.getElementById('settings-ollama-url');
                if (urlInput) urlInput.value = this.settings.ollama_url || 'http://localhost:11434';
                const epubInput = document.getElementById('settings-epub-dir');
                if (epubInput) epubInput.value = this.settings.epub_dir || '';
                modal.classList.remove('hidden');
            });
        }

        if (btnSaveSettings) {
            btnSaveSettings.addEventListener('click', () => {
                this.saveSettings();
                document.getElementById('settings-modal').classList.add('hidden');
            });
        }

        if (btnCloseSettings) {
            btnCloseSettings.addEventListener('click', () => {
                document.getElementById('settings-modal').classList.add('hidden');
            });
        }

        if (btnStartBuild) {
            btnStartBuild.addEventListener('click', () => this.buildKnowledgeBase());
        }

        if (btnCloseBuild) {
            btnCloseBuild.addEventListener('click', () => {
                document.getElementById('build-modal').classList.add('hidden');
                document.getElementById('dir-browser').classList.add('hidden');
            });
        }

        if (btnBrowseDir) {
            btnBrowseDir.addEventListener('click', () => this.openDirBrowser());
        }
        if (btnDirUp) {
            btnDirUp.addEventListener('click', () => {
                const cur = document.getElementById('dir-current').dataset.path || '';
                const parent = document.getElementById('dir-current').dataset.parent || '';
                if (parent) this.browseDirectory(parent);
            });
        }
        if (btnDirSelect) {
            btnDirSelect.addEventListener('click', () => {
                const cur = document.getElementById('dir-current').dataset.path || '';
                if (cur) {
                    document.getElementById('build-epub-dir').value = cur;
                }
                document.getElementById('dir-browser').classList.add('hidden');
            });
        }
        if (btnDirCancel) {
            btnDirCancel.addEventListener('click', () => {
                document.getElementById('dir-browser').classList.add('hidden');
            });
        }

        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', () => {
                overlay.parentElement.classList.add('hidden');
            });
        });
    }

    async saveSettings() {
        try {
            const settings = {
                ollama_url: document.getElementById('settings-ollama-url')?.value || this.settings.ollama_url,
                chat_model: this.settings.chatModel || document.getElementById('select-chat-model')?.value || '',
                embedding_model: document.getElementById('settings-embed-model')?.value || this.settings.embedding_model,
                show_furigana: this.settings.showFurigana,
                romaji_enabled: this.settings.showRomaji,
                current_level: this.settings.currentLevel,
                epub_dir: document.getElementById('settings-epub-dir')?.value || this.settings.epub_dir || '',
                chunk_size: parseInt(document.getElementById('settings-chunk-size')?.value) || 800,
                chunk_overlap: parseInt(document.getElementById('settings-chunk-overlap')?.value) || 150,
                rag_distance_threshold: parseFloat(document.getElementById('settings-rag-threshold')?.value) || 1.5,
            };

            await fetch(`${API}/api/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings),
            });
        } catch (e) {
            console.error('Failed to save settings:', e);
        }
    }

    openDirBrowser() {
        const browser = document.getElementById('dir-browser');
        browser.classList.remove('hidden');
        const currentInput = document.getElementById('build-epub-dir')?.value || '';
        const startPath = currentInput || this.settings.epub_dir || '';
        this.browseDirectory(startPath);
    }

    async browseDirectory(path = '') {
        const listEl = document.getElementById('dir-list');
        const currentEl = document.getElementById('dir-current');
        const countEl = document.getElementById('dir-epub-count');
        const upBtn = document.getElementById('btn-dir-up');
        const selectBtn = document.getElementById('btn-dir-select');

        listEl.innerHTML = '<div class="dir-item">加载中...</div>';
        currentEl.textContent = path || '主目录';
        countEl.textContent = '';

        try {
            const url = `${API}/api/kb/browse?path=${encodeURIComponent(path)}`;
            const resp = await fetch(url);
            const data = await resp.json();

            if (!data.success) {
                listEl.innerHTML = `<div class="dir-item" style="color:var(--danger)">${data.error || '错误'}</div>`;
                upBtn.disabled = !data.parent;
                selectBtn.disabled = true;
                return;
            }

            currentEl.textContent = data.current_path;
            currentEl.dataset.path = data.current_path;
            currentEl.dataset.parent = data.parent || '';

            const quickEl = document.getElementById('dir-quick');
            if (quickEl) {
                quickEl.innerHTML = '';
                (data.quick || []).forEach(q => {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'dir-quick-btn';
                    btn.textContent = q.label;
                    btn.title = q.path;
                    btn.addEventListener('click', () => this.browseDirectory(q.path));
                    quickEl.appendChild(btn);
                });
            }

            upBtn.disabled = !data.parent;
            selectBtn.disabled = false;

            let html = '';
            if (!data.dirs.length && !data.epubs.length) {
                html = '<div class="dir-item" style="opacity:0.6">此目录为空</div>';
            } else {
                data.dirs.forEach(name => {
                    html += `<div class="dir-item" data-name="${this.escapeHtml(name)}"><span class="icon">📁</span><span>${this.escapeHtml(name)}</span></div>`;
                });
                data.epubs.forEach(name => {
                    html += `<div class="dir-item"><span class="icon">📘</span><span>${this.escapeHtml(name)}</span><span class="epub-badge">EPUB</span></div>`;
                });
            }
            listEl.innerHTML = html;

            countEl.textContent = data.has_epubs ? `发现 ${data.epubs.length} 个 EPUB 文件` : '';

            listEl.querySelectorAll('.dir-item[data-name]').forEach(item => {
                item.addEventListener('click', () => {
                    const name = item.dataset.name;
                    const newPath = (data.current_path.replace(/\/$/, '')) + '/' + name;
                    this.browseDirectory(newPath);
                });
            });
        } catch (e) {
            listEl.innerHTML = `<div class="dir-item" style="color:var(--danger)">网络错误：${e.message}</div>`;
        }
    }

    escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    async buildKnowledgeBase() {
        const epubDir = document.getElementById('build-epub-dir')?.value || '';
        const collectionName = document.getElementById('build-collection')?.value || '';
        const progressContainer = document.getElementById('build-progress');
        const progressBar = document.getElementById('build-progress-bar');
        const progressText = document.getElementById('build-progress-text');

        progressContainer.classList.remove('hidden');
        progressBar.style.width = '0%';
        progressText.textContent = '构建中...';

        try {
            const resp = await fetch(`${API}/api/kb/build`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    epub_dir: epubDir,
                    collection_name: collectionName,
                }),
            });

            const data = await resp.json();

            if (data.success) {
                progressBar.style.width = '100%';
                progressText.textContent = `完成！${data.files} 个文件，${data.chunks} 个文本块`;
                this.loadCollections();
                this.loadProgress();
            } else {
                progressText.textContent = `错误：${data.error}`;
                progressBar.style.width = '0%';
            }
        } catch (e) {
            progressText.textContent = `网络错误：${e.message}`;
        }
    }

    async annotateText(text, showFurigana = null, showRomaji = null) {
        try {
            const resp = await fetch(`${API}/api/japanese/annotate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text,
                    show_furigana: showFurigana !== null ? showFurigana : this.settings.showFurigana,
                    show_romaji: showRomaji !== null ? showRomaji : this.settings.showRomaji,
                    learned_kanji: [],
                }),
            });
            return await resp.json();
        } catch (e) {
            console.error('Annotation error:', e);
            return { success: false, error: e.message };
        }
    }
}

const app = new XuehuaApp();