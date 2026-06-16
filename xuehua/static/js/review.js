// Xuehua - Review (SRS) Page JavaScript
const API = '';

class ReviewApp {
    constructor() {
        this.cards = [];
        this.currentIndex = 0;
        this.results = [];
        this.init();
    }

    async init() {
        await this.loadStats();
    }

    async loadStats() {
        try {
            const [srsResp] = await Promise.all([
                fetch(`${API}/api/learning/srs/stats`),
            ]);
            const srs = await srsResp.json();

            const statDue = document.getElementById('stat-due');
            const statLearned = document.getElementById('stat-learned');
            const statTotal = document.getElementById('stat-total');

            if (srs.success && srs.data) {
                if (statDue) statDue.textContent = srs.data.due || 0;
                if (statLearned) statLearned.textContent = srs.data.learned || 0;
                if (statTotal) statTotal.textContent = srs.data.total || 0;
            }
        } catch (e) {
            console.error('Failed to load stats:', e);
        }
    }

    async startReview() {
        try {
            const resp = await fetch(`${API}/api/learning/srs/due?limit=20`);
            const data = await resp.json();

            if (data.success && data.cards && data.cards.length > 0) {
                this.cards = data.cards;
                this.currentIndex = 0;
                this.results = [];
                this.showCard();
            } else {
                await this.addSampleCards();
                const retryResp = await fetch(`${API}/api/learning/srs/due?limit=20`);
                const retryData = await retryResp.json();
                if (retryData.success && retryData.cards && retryData.cards.length > 0) {
                    this.cards = retryData.cards;
                    this.currentIndex = 0;
                    this.results = [];
                    this.showCard();
                } else {
                    alert('暂无待复习的卡片。请先在学习页面添加词汇。');
                }
            }
        } catch (e) {
            console.error('Failed to start review:', e);
            await this.addSampleCards();
        }
    }

    async addSampleCards() {
        const sampleWords = [
            { front: '食べる', back: '吃', reading: 'たべる', level: 'N5', category: 'verb' },
            { front: '飲む', back: '喝', reading: 'のむ', level: 'N5', category: 'verb' },
            { front: '行く', back: '去', reading: 'いく', level: 'N5', category: 'verb' },
            { front: '学生', back: '学生', reading: 'がくせい', level: 'N5', category: 'noun' },
            { front: '先生', back: '老师', reading: 'せんせい', level: 'N5', category: 'noun' },
            { front: '友達', back: '朋友', reading: 'ともだち', level: 'N5', category: 'noun' },
            { front: '大きい', back: '大的', reading: 'おおきい', level: 'N5', category: 'adj-i' },
            { front: '小さい', back: '小的', reading: 'ちいさい', level: 'N5', category: 'adj-i' },
        ];

        for (const word of sampleWords) {
            await fetch(`${API}/api/learning/srs/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(word),
            });
        }
    }

    showCard() {
        const card = this.cards[this.currentIndex];
        if (!card) {
            this.showComplete();
            return;
        }

        const startView = document.getElementById('review-start');
        const cardView = document.getElementById('review-card');
        const completeView = document.getElementById('review-complete');

        startView.classList.add('hidden');
        cardView.classList.remove('hidden');
        completeView.classList.add('hidden');

        const wordEl = document.getElementById('card-word');
        const hintEl = document.getElementById('card-hint');
        const backEl = document.getElementById('card-back');
        const ratingEl = document.getElementById('card-rating');
        const progressFill = document.getElementById('card-progress-fill');
        const progressText = document.getElementById('card-progress-text');

        wordEl.innerHTML = card.front;
        hintEl.textContent = '点击查看答案';
        backEl.classList.add('hidden');
        ratingEl.classList.add('hidden');

        const total = this.cards.length;
        const percent = ((this.currentIndex) / total) * 100;
        progressFill.style.width = `${percent}%`;
        progressText.textContent = `${this.currentIndex + 1} / ${total}`;

        wordEl.onclick = () => {
            hintEl.textContent = '';
            document.getElementById('card-reading').textContent = card.reading || '';
            document.getElementById('card-meaning').textContent = card.back || '';
            document.getElementById('card-example').textContent = '';
            backEl.classList.remove('hidden');
            ratingEl.classList.remove('hidden');
        };
    }

    async rateCard(quality) {
        const card = this.cards[this.currentIndex];
        if (!card) return;

        try {
            await fetch(`${API}/api/learning/srs/review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ card_id: card.card_id, quality }),
            });
        } catch (e) {
            console.error('Failed to rate card:', e);
        }

        this.results.push({ card, quality });
        this.currentIndex++;

        if (this.currentIndex >= this.cards.length) {
            this.showComplete();
        } else {
            this.showCard();
        }
    }

    showComplete() {
        const cardView = document.getElementById('review-card');
        const completeView = document.getElementById('review-complete');
        const summary = document.getElementById('review-summary');

        cardView.classList.add('hidden');
        completeView.classList.remove('hidden');

        const total = this.results.length;
        const correct = this.results.filter(r => r.quality >= 3).length;
        const percent = total > 0 ? Math.round((correct / total) * 100) : 0;

        summary.innerHTML = `
            <div class="review-stats">
                <div class="stat-card">
                    <div class="stat-value">${total}</div>
                    <div class="stat-label">总题数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${correct}</div>
                    <div class="stat-label">正确</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${percent}%</div>
                    <div class="stat-label">正确率</div>
                </div>
            </div>
        `;

        this.loadStats();
    }
}

const reviewApp = new ReviewApp();

function startReview() { reviewApp.startReview(); }
function rateCard(quality) { reviewApp.rateCard(quality); }