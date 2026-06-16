// Xuehua - Chat Page JavaScript
const API = '';

class ChatApp {
    constructor() {
        this.messages = [];
        this.isStreaming = false;
        this.abortController = null;
        this.collections = [];
        this.init();
    }

    async init() {
        this.bindEvents();
        this.loadCollections();
        this.loadModels();
        this.autoResizeInput();
    }

    bindEvents() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('btn-send');

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        input.addEventListener('input', () => this.autoResizeInput());
    }

    autoResizeInput() {
        const input = document.getElementById('chat-input');
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    }

    async loadModels() {
        try {
            const resp = await fetch(`${API}/api/models`);
            const data = await resp.json();
            const select = document.getElementById('chat-model-select');
            if (select && data.chatModels) {
                select.innerHTML = '';
                data.chatModels.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m;
                    if (m === data.currentChat) opt.selected = true;
                    select.appendChild(opt);
                });
            }
        } catch (e) {
            console.error('Failed to load models:', e);
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
                        `<label class="toggle-label"><input type="checkbox" class="kb-check" value="${c.name}" checked> ${c.name} (${c.count})</label>`
                    ).join('');
                }
            }
        } catch (e) {
            console.error('Failed to load collections:', e);
        }
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (!message || this.isStreaming) return;

        input.value = '';
        this.autoResizeInput();

        this.addMessage('user', message);

        const useKB = document.getElementById('chat-use-kb')?.checked ?? true;
        const collections = Array.from(document.querySelectorAll('.kb-check:checked')).map(cb => cb.value);

        const modelSelect = document.getElementById('chat-model-select');
        const model = modelSelect ? modelSelect.value : '';

        this.isStreaming = true;
        this.showStopButton();

        const assistantEl = this.addMessage('assistant', '');
        const contentEl = assistantEl.querySelector('.msg-content') || assistantEl;

        try {
            const resp = await fetch(`${API}/api/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    model: model || undefined,
                    use_kb: useKB,
                    collections: collections.length > 0 ? collections : undefined,
                }),
            });

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;
                contentEl.innerHTML = this.renderMarkdown(fullText);
                this.scrollToBottom();
            }
        } catch (e) {
            if (e.name !== 'AbortError') {
                contentEl.textContent = `错误：${e.message}`;
            }
        } finally {
            this.isStreaming = false;
            this.hideStopButton();
        }
    }

    stopGeneration() {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
    }

    addMessage(role, content) {
        const container = document.getElementById('chat-messages');
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg ${role}`;

        if (content) {
            msgDiv.innerHTML = `<div class="msg-content">${this.renderMarkdown(content)}</div>`;
        } else {
            msgDiv.innerHTML = '<div class="msg-content"></div>';
        }

        container.appendChild(msgDiv);
        this.scrollToBottom();
        return msgDiv;
    }

    renderMarkdown(text) {
        let html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="$1">$2</code></pre>');
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/\n/g, '<br>');

        return html;
    }

    scrollToBottom() {
        const container = document.getElementById('chat-messages');
        container.scrollTop = container.scrollHeight;
    }

    showStopButton() {
        document.getElementById('btn-send')?.classList.add('hidden');
        document.getElementById('btn-stop')?.classList.remove('hidden');
    }

    hideStopButton() {
        document.getElementById('btn-send')?.classList.remove('hidden');
        document.getElementById('btn-stop')?.classList.add('hidden');
    }
}

const chatApp = new ChatApp();

function sendMessage() { chatApp.sendMessage(); }
function stopGeneration() { chatApp.stopGeneration(); }