// Xuehua - Learning Page JavaScript
const API = '';

class LearnApp {
    constructor() {
        this.currentLevel = 'N5';
        this.currentTab = 'domains';
        this.currentDomain = '';
        this.domains = [];
        this.domainWords = [];
        this.quizState = { questions: [], current: 0, score: 0 };
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadDomains();
    }

    bindEvents() {
        document.querySelectorAll('.level-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.level-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentLevel = btn.dataset.level;
                if (this.currentDomain) {
                    this.loadDomainWords(this.currentDomain);
                }
            });
        });

        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
                const tab = btn.dataset.tab;
                document.getElementById(`tab-${tab}`).classList.add('active');
                this.currentTab = tab;
            });
        });
    }

    async loadDomains() {
        try {
            const resp = await fetch(`${API}/api/vocab/domains`);
            const data = await resp.json();
            if (data.success) {
                this.domains = data.domains;
                this.renderDomains();
            }
        } catch (e) {
            console.error('Failed to load domains:', e);
            this.renderDomains();
        }
    }

    renderDomains() {
        const container = document.getElementById('vocab-list');
        if (!container) return;

        container.innerHTML = this.domains.map(d => `
            <div class="domain-card" onclick="learnApp.loadDomainWords('${d.domain_id}')" style="cursor:pointer; background:var(--card-bg); border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="font-size:1.5em;">${d.center_words.slice(0,3).map(w => `<ruby>${w}<rp>(</rp><rt></rt><rp>)</rp></ruby>`).join(' ')}</div>
                    <div style="flex:1;">
                        <h3 style="margin:0; font-size:1.1em;">${d.domain_name} ${d.domain_name_ja}</h3>
                        <p style="margin:4px 0 0; font-size:0.85em; color:var(--text-secondary);">${d.description}</p>
                        <div style="margin-top:6px; display:flex; gap:8px; font-size:0.8em; color:var(--text-muted);">
                            <span>${d.word_count} 词汇</span>
                            <span>级别: ${d.levels.join(', ')}</span>
                        </div>
                    </div>
                    <div style="color:var(--accent); font-size:1.5em;">→</div>
                </div>
            </div>
        `).join('');
    }

    async loadDomainWords(domainId) {
        this.currentDomain = domainId;
        const level = this.currentLevel;

        try {
            const resp = await fetch(`${API}/api/vocab/domain/${domainId}/words?level=${level}`);
            const data = await resp.json();
            if (data.success) {
                this.domainWords = data.words;
                this.renderDomainWords(domainId);
            }
        } catch (e) {
            console.error('Failed to load domain words:', e);
        }
    }

    renderDomainWords(domainId) {
        const domain = this.domains.find(d => d.domain_id === domainId);
        const container = document.getElementById('vocab-list');
        if (!container) return;

        const backBtn = `<button class="btn btn-secondary" onclick="learnApp.renderDomains(); learnApp.currentDomain='';" style="margin-bottom:16px;">← 返回领域列表</button>`;
        const header = `<div style="margin-bottom:16px;"><h3>${domain ? domain.domain_name : ''} ${domain ? domain.domain_name_ja : ''}</h3><p style="color:var(--text-secondary);font-size:0.9em;">${domain ? domain.description : ''}</p></div>`;

        const networkMap = this.renderNetworkMap();

        const wordCards = this.domainWords.map((w, i) => `
            <div class="vocab-card" onclick="learnApp.showWordDetail(${i})">
                <div class="vocab-word">${w.html_ruby || w.word}</div>
                <div class="vocab-reading">${w.reading}</div>
                <div class="vocab-meaning">${w.meaning}</div>
                <div style="font-size:0.75em; color:var(--text-muted); margin-top:4px;">${w.level} · ${w.pos}</div>
                ${w.html_romaji ? `<div style="font-size:0.8em; color:var(--text-muted); margin-top:2px;">${w.html_romaji}</div>` : ''}
            </div>
        `).join('');

        container.innerHTML = `${backBtn}${header}${networkMap}<div class="vocab-grid">${wordCards}</div>`;
    }

    renderNetworkMap() {
        if (!this.domainWords.length) return '';

        const centerWords = this.domainWords.filter(w => w.related && w.related.length > 3);
        if (!centerWords.length) return '';

        const nodes = this.domainWords.map(w => ({
            id: w.word,
            label: w.word,
            reading: w.reading,
            meaning: w.meaning,
            isCenter: w.related && w.related.length > 3,
        }));

        const edges = [];
        const wordSet = new Set(this.domainWords.map(w => w.word));
        for (const w of this.domainWords) {
            if (w.related) {
                for (const rel of w.related) {
                    if (wordSet.has(rel)) {
                        edges.push({ source: w.word, target: rel });
                    }
                }
            }
        }

        let html = '<div class="network-map" style="background:var(--bg-tertiary); border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:16px; overflow-x:auto;">';
        html += '<div style="display:flex; flex-wrap:wrap; gap:8px; justify-content:center; align-items:center;">';

        const centerNodes = nodes.filter(n => n.isCenter);
        const otherNodes = nodes.filter(n => !n.isCenter);

        for (const node of centerNodes) {
            html += `<div style="background:var(--accent); color:white; padding:6px 14px; border-radius:20px; font-size:0.95em; font-weight:600; cursor:pointer;" onclick="learnApp.showWordByWord('${node.id}')">${node.label}<br><span style="font-size:0.75em; opacity:0.8;">${node.reading}</span></div>`;
        }

        html += '<div style="width:100%;"></div>';

        for (const node of otherNodes) {
            html += `<div style="background:var(--bg-primary); border:1px solid var(--border); padding:4px 10px; border-radius:12px; font-size:0.85em; cursor:pointer;" onclick="learnApp.showWordByWord('${node.id}')">${node.label} <span style="font-size:0.75em; color:var(--text-muted);">${node.reading}</span></div>`;
        }

        html += '</div></div>';
        return html;
    }

    showWordDetail(index) {
        const w = this.domainWords[index];
        if (!w) return;

        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.classList.add('hidden'); this.parentElement.remove();"></div>
            <div class="modal-content" style="max-width:600px;">
                <h2 style="margin-bottom:8px;">${w.html_ruby || w.word}</h2>
                <div style="font-size:1.3em; color:var(--accent); margin-bottom:8px;">${w.reading}</div>
                ${w.html_romaji ? `<div style="font-size:1em; color:var(--text-muted); margin-bottom:12px;">${w.html_romaji}</div>` : ''}
                <div style="font-size:1.1em; margin-bottom:12px;">${w.meaning}</div>
                <div style="font-size:0.85em; color:var(--text-secondary); margin-bottom:6px;">
                    <span style="background:var(--accent); color:white; padding:2px 8px; border-radius:4px; font-size:0.8em;">${w.level}</span>
                    <span style="margin-left:8px;">${w.pos}</span>
                </div>
                ${w.example_jp ? `
                <div style="background:var(--bg-tertiary); border-radius:8px; padding:12px; margin-top:12px;">
                    <div style="font-size:0.85em; color:var(--text-muted); margin-bottom:4px;">例文</div>
                    <div style="font-size:1.1em; line-height:1.8;">${w.example_jp}</div>
                    ${w.example_reading ? `<div style="font-size:0.9em; color:var(--text-secondary);">${w.example_reading}</div>` : ''}
                    <div style="font-size:0.95em; color:var(--text-secondary); margin-top:4px;">${w.example_zh}</div>
                </div>
                ` : ''}
                ${w.related && w.related.length ? `
                <div style="margin-top:12px;">
                    <div style="font-size:0.85em; color:var(--text-muted); margin-bottom:6px;">关联词汇</div>
                    <div style="display:flex; flex-wrap:wrap; gap:6px;">
                        ${w.related.map(r => `<span style="background:var(--bg-primary); border:1px solid var(--border); padding:3px 10px; border-radius:12px; font-size:0.85em; cursor:pointer;" onclick="learnApp.searchWord('${r}')">${r}</span>`).join('')}
                    </div>
                </div>
                ` : ''}
                <div style="margin-top:16px; display:flex; gap:8px;">
                    <button class="btn btn-primary" onclick="learnApp.addToSRS('${w.word}', '${w.meaning}', '${w.reading}', '${w.level}', '${this.currentDomain}')">加入复习</button>
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">关闭</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.classList.remove('hidden');
    }

    showWordByWord(wordStr) {
        const idx = this.domainWords.findIndex(w => w.word === wordStr);
        if (idx >= 0) {
            this.showWordDetail(idx);
        }
    }

    async searchWord(word) {
        try {
            const resp = await fetch(`${API}/api/vocab/search?q=${encodeURIComponent(word)}`);
            const data = await resp.json();
            if (data.success && data.results.length > 0) {
                const r = data.results[0];
                const modal = document.createElement('div');
                modal.className = 'modal';
                modal.innerHTML = `
                    <div class="modal-overlay" onclick="this.parentElement.classList.add('hidden'); this.parentElement.remove();"></div>
                    <div class="modal-content" style="max-width:500px;">
                        <h3>${r.html_ruby || r.word}</h3>
                        <div style="font-size:1.2em; color:var(--accent);">${r.reading}</div>
                        <div style="font-size:1.1em; margin:8px 0;">${r.meaning}</div>
                        <div style="font-size:0.85em; color:var(--text-secondary);">${r.level} · ${r.pos}</div>
                        ${r.example_jp ? `<div style="margin-top:8px; padding:8px; background:var(--bg-tertiary); border-radius:6px;">${r.example_jp}<br><span style="color:var(--text-secondary);">${r.example_zh}</span></div>` : ''}
                        <button class="btn btn-secondary" style="margin-top:12px;" onclick="this.closest('.modal').remove()">关闭</button>
                    </div>
                `;
                document.body.appendChild(modal);
                modal.classList.remove('hidden');
            }
        } catch (e) {
            console.error('Search failed:', e);
        }
    }

    async addToSRS(front, back, reading, level, category) {
        try {
            await fetch(`${API}/api/learning/srs/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ front, back, reading, level, category }),
            });
            alert('已加入复习计划！');
        } catch (e) {
            console.error('Failed to add card:', e);
        }
    }

    async startQuiz(type) {
        const words = this.domainWords.length > 0 ? this.domainWords : this.getSampleVocabulary(this.currentLevel);
        if (words.length < 4) {
            alert('词汇不足，请先选择一个领域');
            return;
        }

        const vocab = words.map(w => ({
            word: w.word,
            meaning: w.meaning,
            reading: w.reading,
            level: w.level,
        }));

        if (type === 'multiple_choice') {
            const resp = await fetch(`${API}/api/exercises/multiple_choice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items: vocab, num_choices: 4 }),
            });
            const data = await resp.json();
            if (data.success) {
                this.quizState.questions = data.exercises;
                this.quizState.current = 0;
                this.quizState.score = 0;
            }
        } else if (type === 'reading') {
            const resp = await fetch(`${API}/api/exercises/reading_quiz`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vocabulary: vocab }),
            });
            const data = await resp.json();
            if (data.success) {
                this.quizState.questions = data.exercises;
                this.quizState.current = 0;
                this.quizState.score = 0;
            }
        }

        const quizArea = document.getElementById('quiz-area');
        const quizStart = quizArea.querySelector('.quiz-start');
        const quizContent = document.getElementById('quiz-content');

        quizStart.classList.add('hidden');
        quizContent.classList.remove('hidden');
        this.showQuizQuestion();
    }

    showQuizQuestion() {
        const q = this.quizState.questions[this.quizState.current];
        if (!q) { this.showQuizResult(); return; }

        const questionEl = document.getElementById('quiz-question');
        const choicesEl = document.getElementById('quiz-choices');
        const feedbackEl = document.getElementById('quiz-feedback');
        const progressEl = document.getElementById('quiz-progress');
        const nextBtn = document.getElementById('btn-next-quiz');

        questionEl.innerHTML = q.question;
        feedbackEl.classList.add('hidden');
        nextBtn.classList.add('hidden');

        choicesEl.innerHTML = q.choices.map((c, i) =>
            `<button class="quiz-choice" onclick="learnApp.checkAnswer(${i})">${c}</button>`
        ).join('');

        progressEl.textContent = `${this.quizState.current + 1} / ${this.quizState.questions.length}`;
    }

    checkAnswer(selectedIndex) {
        const q = this.quizState.questions[this.quizState.current];
        if (!q) return;

        const choices = document.querySelectorAll('.quiz-choice');
        const feedbackEl = document.getElementById('quiz-feedback');
        const nextBtn = document.getElementById('btn-next-quiz');

        choices.forEach((c, i) => {
            if (i === q.correct_index) c.classList.add('correct');
            else if (i === selectedIndex && i !== q.correct_index) c.classList.add('wrong');
            c.disabled = true;
        });

        const correct = selectedIndex === q.correct_index;
        if (correct) this.quizState.score++;

        feedbackEl.classList.remove('hidden');
        feedbackEl.className = `quiz-feedback ${correct ? 'correct' : 'wrong'}`;
        feedbackEl.textContent = correct ? '✓ 正确！' : `✗ 正确答案是：${q.choices[q.correct_index]}`;

        nextBtn.classList.remove('hidden');
    }

    nextQuiz() {
        this.quizState.current++;
        if (this.quizState.current >= this.quizState.questions.length) {
            this.showQuizResult();
        } else {
            this.showQuizQuestion();
        }
    }

    showQuizResult() {
        const total = this.quizState.questions.length;
        const score = this.quizState.score;
        const percent = total > 0 ? Math.round((score / total) * 100) : 0;

        const quizContent = document.getElementById('quiz-content');
        quizContent.innerHTML = `
            <div style="text-align:center; padding:40px;">
                <h3>测验完成！</h3>
                <p style="font-size:2em; margin:16px 0;">${score} / ${total}</p>
                <p style="color:var(--text-secondary);">正确率：${percent}%</p>
                <button class="btn btn-primary" onclick="location.reload()">继续学习</button>
            </div>
        `;
    }

    getSampleVocabulary(level) {
        const vocabData = {
            N5: [
                { word: '食べる', reading: 'たべる', meaning: '吃', level: 'N5' },
                { word: '飲む', reading: 'のむ', meaning: '喝', level: 'N5' },
                { word: '行く', reading: 'いく', meaning: '去', level: 'N5' },
                { word: '来る', reading: 'くる', meaning: '来', level: 'N5' },
                { word: '見る', reading: 'みる', meaning: '看', level: 'N5' },
                { word: '学生', reading: 'がくせい', meaning: '学生', level: 'N5' },
                { word: '友達', reading: 'ともだち', meaning: '朋友', level: 'N5' },
                { word: '大きい', reading: 'おおきい', meaning: '大的', level: 'N5' },
            ],
            N4: [
                { word: '経験', reading: 'けいけん', meaning: '经验', level: 'N4' },
                { word: '説明', reading: 'せつめい', meaning: '说明', level: 'N4' },
                { word: '練習', reading: 'れんしゅう', meaning: '练习', level: 'N4' },
                { word: '趣味', reading: 'しゅみ', meaning: '兴趣', level: 'N4' },
            ],
        };
        return vocabData[level] || vocabData.N5;
    }
}

const learnApp = new LearnApp();

function startQuiz(type) { learnApp.startQuiz(type); }
function nextQuiz() { learnApp.nextQuiz(); }