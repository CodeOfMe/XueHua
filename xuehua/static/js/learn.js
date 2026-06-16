// Xuehua - Learning Page JavaScript
const API = '';

class LearnApp {
    constructor() {
        this.currentLevel = 'N5';
        this.currentTab = 'vocabulary';
        this.vocabulary = [];
        this.quizState = { questions: [], current: 0, score: 0 };
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadVocabulary();
    }

    bindEvents() {
        document.querySelectorAll('.level-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.level-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentLevel = btn.dataset.level;
                this.loadVocabulary();
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

    async loadVocabulary() {
        const container = document.getElementById('vocab-list');
        if (!container) return;

        container.innerHTML = '<div class="loading">加载中...</div>';

        const sampleVocab = this.getSampleVocabulary(this.currentLevel);

        try {
            const resp = await fetch(`${API}/api/japanese/annotate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: sampleVocab.map(v => v.word).join('、'),
                    show_furigana: true,
                    show_romaji: false,
                    learned_kanji: [],
                }),
            });
            const data = await resp.json();

            if (data.success) {
                const annotatedWords = data.tokens || [];
                this.renderVocabulary(sampleVocab, annotatedWords);
            } else {
                this.renderVocabulary(sampleVocab, null);
            }
        } catch (e) {
            this.renderVocabulary(sampleVocab, null);
        }
    }

    renderVocabulary(vocab, annotatedTokens) {
        const container = document.getElementById('vocab-list');
        if (!container) return;

        container.innerHTML = vocab.map((item, i) => {
            const word = item.word;
            const reading = item.reading;
            const meaning = item.meaning;

            return `
                <div class="vocab-card" onclick="learnApp.showVocabDetail(${i})">
                    <div class="vocab-word"><ruby>${word}<rp>(</rp><rt>${reading}</rt><rp>)</rp></ruby></div>
                    <div class="vocab-reading">${reading}</div>
                    <div class="vocab-meaning">${meaning}</div>
                </div>
            `;
        }).join('');
    }

    showVocabDetail(index) {
        const item = this.getSampleVocabulary(this.currentLevel)[index];
        if (!item) return;

        const detail = document.getElementById('vocab-detail');
        if (!detail) {
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-overlay" onclick="this.parentElement.classList.add('hidden')"></div>
                <div class="modal-content">
                    <h2 id="detail-word"></h2>
                    <div id="detail-reading" style="font-size:1.5em;color:var(--accent);margin:8px 0"></div>
                    <div id="detail-meaning" style="font-size:1.2em;margin:8px 0"></div>
                    <div id="detail-example" style="margin:16px 0;color:var(--text-secondary);line-height:1.8"></div>
                    <button class="btn btn-secondary" onclick="this.closest('.modal').classList.add('hidden')">关闭</button>
                </div>
            `;
            document.body.appendChild(modal);
        }

        const wordEl = document.getElementById('detail-word');
        const readEl = document.getElementById('detail-reading');
        const meanEl = document.getElementById('detail-meaning');
        const exEl = document.getElementById('detail-example');

        wordEl.innerHTML = `<ruby>${item.word}<rp>(</rp><rt>${item.reading}</rt><rp>)</rp></ruby>`;
        readEl.textContent = item.reading;
        meanEl.textContent = item.meaning;
        exEl.textContent = item.example || '';

        const modal = document.querySelector('.modal:last-of-type');
        if (modal) modal.classList.remove('hidden');
    }

    async startQuiz(type) {
        const vocab = this.getSampleVocabulary(this.currentLevel);
        if (vocab.length < 4) {
            alert('词汇不足，请先构建知识库或选择更高级别');
            return;
        }

        const quizArea = document.getElementById('quiz-area');
        const quizStart = quizArea.querySelector('.quiz-start');
        const quizContent = document.getElementById('quiz-content');

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

        quizStart.classList.add('hidden');
        quizContent.classList.remove('hidden');
        this.showQuizQuestion();
    }

    showQuizQuestion() {
        const q = this.quizState.questions[this.quizState.current];
        if (!q) {
            this.showQuizResult();
            return;
        }

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
            if (i === q.correct_index) {
                c.classList.add('correct');
            } else if (i === selectedIndex && i !== q.correct_index) {
                c.classList.add('wrong');
            }
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
        const percent = Math.round((score / total) * 100);

        const quizContent = document.getElementById('quiz-content');
        quizContent.innerHTML = `
            <div style="text-align:center;padding:40px">
                <h3>测验完成！</h3>
                <p style="font-size:2em;margin:16px 0">${score} / ${total}</p>
                <p style="color:var(--text-secondary)">正确率：${percent}%</p>
                <button class="btn btn-primary" onclick="location.reload()">继续学习</button>
            </div>
        `;
    }

    getSampleVocabulary(level) {
        const vocabData = {
            N5: [
                { word: '食べる', reading: 'たべる', meaning: '吃', example: '朝ごはんを食べる。', level: 'N5' },
                { word: '飲む', reading: 'のむ', meaning: '喝', example: '水を飲む。', level: 'N5' },
                { word: '行く', reading: 'いく', meaning: '去', example: '学校に行く。', level: 'N5' },
                { word: '来る', reading: 'くる', meaning: '来', example: '友達が来る。', level: 'N5' },
                { word: '見る', reading: 'みる', meaning: '看', example: 'テレビを見る。', level: 'N5' },
                { word: '聞く', reading: 'きく', meaning: '听/问', example: '音楽を聞く。', level: 'N5' },
                { word: '読む', reading: 'よむ', meaning: '读', example: '本を読む。', level: 'N5' },
                { word: '書く', reading: 'かく', meaning: '写', example: '手紙を書く。', level: 'N5' },
                { word: '話す', reading: 'はなす', meaning: '说话', example: '日本語を話す。', level: 'N5' },
                { word: '買う', reading: 'かう', meaning: '买', example: 'パンを買う。', level: 'N5' },
                { word: '学生', reading: 'がくせい', meaning: '学生', example: '私は学生です。', level: 'N5' },
                { word: '先生', reading: 'せんせい', meaning: '老师', example: '先生に聞く。', level: 'N5' },
                { word: '友達', reading: 'ともだち', meaning: '朋友', example: '友達と遊ぶ。', level: 'N5' },
                { word: '大きい', reading: 'おおきい', meaning: '大的', example: '大きい家。', level: 'N5' },
                { word: '小さい', reading: 'ちいさい', meaning: '小的', example: '小さい猫。', level: 'N5' },
                { word: '美味しい', reading: 'おいしい', meaning: '好吃的', example: '美味しい料理。', level: 'N5' },
            ],
            N4: [
                { word: '経験', reading: 'けいけん', meaning: '经验', example: '経験を積む。', level: 'N4' },
                { word: '説明', reading: 'せつめい', meaning: '说明', example: '詳しく説明する。', level: 'N4' },
                { word: '練習', reading: 'れんしゅう', meaning: '练习', example: '毎日練習する。', level: 'N4' },
                { word: '約束', reading: 'やくそく', meaning: '约定', example: '約束を守る。', level: 'N4' },
                { word: '連絡', reading: 'れんらく', meaning: '联系', example: '電話で連絡する。', level: 'N4' },
                { word: '準備', reading: 'じゅんび', meaning: '准备', example: '旅行の準備をする。', level: 'N4' },
                { word: '紹介', reading: 'しょうかい', meaning: '介绍', example: '自己紹介をする。', level: 'N4' },
                { word: '趣味', reading: 'しゅみ', meaning: '兴趣/爱好', example: '趣味は読書です。', level: 'N4' },
            ],
            N3: [
                { word: '影響', reading: 'えいきょう', meaning: '影响', example: '環境に影響する。', level: 'N3' },
                { word: '可能性', reading: 'かのうせい', meaning: '可能性', example: '可能性が高い。', level: 'N3' },
                { word: '努力', reading: 'どりょく', meaning: '努力', example: '努力が必要だ。', level: 'N3' },
                { word: '表現', reading: 'ひょうげん', meaning: '表现/表达', example: '感情を表現する。', level: 'N3' },
            ],
            N2: [
                { word: '推測', reading: 'すいそく', meaning: '推测', example: '原因を推測する。', level: 'N2' },
                { word: '維持', reading: 'いじ', meaning: '维持', example: '品質を維持する。', level: 'N2' },
            ],
            N1: [
                { word: '遣憾', reading: 'いかん', meaning: '遗憾', example: '遣憾に思う。', level: 'N1' },
                { word: '齟齬', reading: 'そご', meaning: '不一致/矛盾', example: '認識の齟齬。', level: 'N1' },
            ],
        };
        return vocabData[level] || vocabData.N5;
    }
}

const learnApp = new LearnApp();

function startQuiz(type) { learnApp.startQuiz(type); }
function nextQuiz() { learnApp.nextQuiz(); }