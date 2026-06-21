var API = API || '';
let imageData = null;
let identifiedItems = [];
let currentVisionModel = "";

async function init() {
    await loadModels();
    setupDragDrop();
}

async function loadModels() {
    const statusEl = document.getElementById("model-status");
    const modelSelect = document.getElementById("vision-model");
    try {
        const resp = await fetch("/api/photo/models");
        const data = await resp.json();
        if (data.success && data.available) {
            statusEl.textContent = "Ollama 已连接";
            statusEl.style.color = "var(--success)";
            modelSelect.innerHTML = '<option value="">自动选择</option>';
            if (data.vision_models && data.vision_models.length > 0) {
                const optgroup = document.createElement("optgroup");
                optgroup.label = "视觉模型（推荐）";
                data.vision_models.forEach(m => {
                    const opt = document.createElement("option");
                    opt.value = m;
                    opt.textContent = m;
                    optgroup.appendChild(opt);
                });
                modelSelect.appendChild(optgroup);
            }
            if (data.chat_models && data.chat_models.length > 0) {
                const optgroup = document.createElement("optgroup");
                optgroup.label = "文本模型";
                data.chat_models.forEach(m => {
                    const opt = document.createElement("option");
                    opt.value = m;
                    opt.textContent = m;
                    optgroup.appendChild(opt);
                });
                modelSelect.appendChild(optgroup);
            }
            if (data.recommended) {
                currentVisionModel = data.recommended;
            }
        } else {
            statusEl.textContent = "Ollama 未连接";
            statusEl.style.color = "var(--danger)";
        }
    } catch (e) {
        statusEl.textContent = "Ollama 未连接";
        statusEl.style.color = "var(--danger)";
    }
}

function setupDragDrop() {
    const area = document.getElementById("upload-area");
    const fileInput = document.getElementById("photo-input");

    area.addEventListener("click", (e) => {
        if (!area.classList.contains("has-image")) {
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    });

    area.addEventListener("dragover", (e) => {
        e.preventDefault();
        area.classList.add("dragover");
    });

    area.addEventListener("dragleave", () => {
        area.classList.remove("dragover");
    });

    area.addEventListener("drop", (e) => {
        e.preventDefault();
        area.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
}

async function handleFile(file) {
    const allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    if (!allowed.includes(file.type)) {
        showError("不支持的图片格式，请使用 JPG/PNG/WebP");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);

    try {
        showLoading("处理图片中...");
        const resp = await fetch("/api/photo/upload", {
            method: "POST",
            body: formData,
        });
        const data = await resp.json();
        hideLoading();

        if (data.success) {
            imageData = data.image_data;
            const preview = document.getElementById("preview-image");
            preview.src = "data:" + file.type + ";base64," + imageData;
            preview.classList.remove("hidden");

            document.getElementById("upload-prompt").classList.add("hidden");
            document.getElementById("image-actions").classList.remove("hidden");
            document.getElementById("upload-area").classList.add("has-image");

            document.getElementById("btn-identify").disabled = false;
            hideError();
        } else {
            showError(data.error || "上传失败");
        }
    } catch (e) {
        hideLoading();
        showError("上传失败: " + e.message);
    }
}

function clearImage() {
    imageData = null;
    identifiedItems = [];
    document.getElementById("preview-image").classList.add("hidden");
    document.getElementById("preview-image").src = "";
    document.getElementById("upload-prompt").classList.remove("hidden");
    document.getElementById("image-actions").classList.add("hidden");
    document.getElementById("upload-area").classList.remove("has-image");
    document.getElementById("btn-identify").disabled = true;
    document.getElementById("identify-result").classList.add("hidden");
    document.getElementById("lesson-result").classList.add("hidden");
    document.getElementById("photo-input").value = "";
    hideError();
}

function reselectImage() {
    clearImage();
    document.getElementById("photo-input").click();
}

async function identifyImage() {
    if (!imageData) {
        showError("请先上传或拍照一张图片");
        return;
    }

    const model = document.getElementById("vision-model").value || "";
    showLoading("正在识别图片中的物品...");

    try {
        const resp = await fetch("/api/photo/identify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: imageData, model: model }),
        });
        const data = await resp.json();
        hideLoading();

        if (data.success) {
            identifiedItems = data.items || [];
            renderIdentifyResult(data.scene_description, identifiedItems);
            hideError();
        } else {
            showError(data.error || "识别失败");
        }
    } catch (e) {
        hideLoading();
        showError("识别失败: " + e.message);
    }
}

function renderIdentifyResult(sceneDesc, items) {
    const resultEl = document.getElementById("identify-result");
    resultEl.classList.remove("hidden");

    const sceneEl = document.getElementById("scene-desc");
    if (sceneDesc) {
        document.getElementById("scene-text").textContent = sceneDesc;
        sceneEl.classList.remove("hidden");
    } else {
        sceneEl.classList.add("hidden");
    }

    const grid = document.getElementById("items-grid");
    grid.innerHTML = "";

    items.forEach((item, idx) => {
        const card = document.createElement("div");
        card.className = "item-card";
        card.onclick = () => showWordDetail(item);
        card.innerHTML = `
            <div class="item-word">${item.name}</div>
            <div class="item-pinyin">${item.pinyin}</div>
            ${item.english ? '<div class="item-english">' + item.english + "</div>" : ""}
            ${item.explanation ? '<div class="item-explanation">' + item.explanation + "</div>" : ""}
        `;
        grid.appendChild(card);
    });

    document.getElementById("lesson-result").classList.add("hidden");
}

async function generateLesson() {
    if (identifiedItems.length === 0) {
        showError("没有识别到物品");
        return;
    }

    const model = document.getElementById("vision-model").value || "";
    showLoading("正在生成学习课程...");

    try {
        const resp = await fetch("/api/photo/lesson", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ items: identifiedItems, model: model }),
        });
        const data = await resp.json();
        hideLoading();

        if (data.success) {
            renderLesson(data.lesson);
            hideError();
        } else {
            showError(data.error || "生成课程失败");
        }
    } catch (e) {
        hideLoading();
        showError("生成课程失败: " + e.message);
    }
}

function renderLesson(lesson) {
    const lessonEl = document.getElementById("lesson-result");
    lessonEl.classList.remove("hidden");

    document.getElementById("lesson-title").textContent = lesson.title || "今日识字课";

    const chantEl = document.getElementById("lesson-chant");
    if (lesson.chant) {
        chantEl.textContent = lesson.chant;
        chantEl.classList.remove("hidden");
    } else {
        chantEl.classList.add("hidden");
    }

    const wordsContainer = document.getElementById("lesson-words");
    wordsContainer.innerHTML = "";

    (lesson.words || []).forEach(w => {
        const card = document.createElement("div");
        card.className = "lesson-word-card";

        let metaHtml = "";
        if (w.radical) metaHtml += '<span class="lwc-meta-item">部首: ' + w.radical + "</span>";
        if (w.strokes) metaHtml += '<span class="lwc-meta-item">笔画: ' + w.strokes + "</span>";

        let exampleHtml = "";
        if (w.example_sentence) {
            exampleHtml = '<div class="lwc-example"><div class="lwc-example-zh">' + w.example_sentence + "</div>";
            if (w.example_pinyin) exampleHtml += '<div class="lwc-example-py">' + w.example_pinyin + "</div>";
            if (w.example_translation) exampleHtml += '<div class="lwc-example-en">' + w.example_translation + "</div>";
            exampleHtml += "</div>";
        }

        let funFactHtml = "";
        if (w.fun_fact) funFactHtml = '<div class="lwc-fun-fact">💡 ' + w.fun_fact + "</div>";

        let strokeHtml = "";
        if (w.stroke_order_hint) strokeHtml = '<div class="lwc-stroke">✏️ 笔顺: ' + w.stroke_order_hint + "</div>";

        let relatedHtml = "";
        if (w.related_words && w.related_words.length > 0) {
            relatedHtml = '<div class="lwc-related">';
            w.related_words.forEach(rw => {
                relatedHtml += '<span class="related-tag">' + rw + "</span>";
            });
            relatedHtml += "</div>";
        }

        card.innerHTML = `
            <div class="lwc-header">
                <span class="lwc-word">${w.word}</span>
                <span class="lwc-pinyin">${w.pinyin}</span>
            </div>
            <div class="lwc-meaning">${w.meaning || ""}</div>
            ${metaHtml ? '<div class="lwc-meta">' + metaHtml + "</div>" : ""}
            ${exampleHtml}
            ${funFactHtml}
            ${strokeHtml}
            ${relatedHtml}
        `;
        wordsContainer.appendChild(card);
    });

    const storyEl = document.getElementById("lesson-story");
    if (lesson.story) {
        storyEl.innerHTML = "<h4>📖 小故事</h4><p>" + lesson.story + "</p>";
        storyEl.classList.remove("hidden");
    } else {
        storyEl.classList.add("hidden");
    }

    const questionsEl = document.getElementById("lesson-questions");
    if (lesson.questions && lesson.questions.length > 0) {
        const list = document.getElementById("questions-list");
        list.innerHTML = "";
        lesson.questions.forEach(q => {
            const li = document.createElement("li");
            li.textContent = q;
            list.appendChild(li);
        });
        questionsEl.classList.remove("hidden");
    } else {
        questionsEl.classList.add("hidden");
    }

    lessonEl.scrollIntoView({ behavior: "smooth" });
}

function showWordDetail(item) {
    document.getElementById("detail-word").textContent = item.name;
    document.getElementById("detail-pinyin").textContent = item.pinyin;
    document.getElementById("detail-radical").textContent = item.radical || "-";
    document.getElementById("detail-strokes").textContent = item.strokes || "-";
    document.getElementById("detail-english").textContent = item.english || "";
    document.getElementById("detail-explanation").textContent = item.explanation || "";

    const exampleEl = document.getElementById("detail-example");
    const examplePyEl = document.getElementById("detail-example-pinyin");
    if (item.example) {
        exampleEl.textContent = item.example;
        examplePyEl.textContent = item.example_pinyin || "";
        exampleEl.parentElement.style.display = "block";
    } else {
        exampleEl.parentElement.style.display = "none";
    }

    document.getElementById("word-detail-modal").classList.remove("hidden");
}

function closeWordDetail() {
    document.getElementById("word-detail-modal").classList.add("hidden");
}

function showLoading(text) {
    const el = document.getElementById("loading");
    document.getElementById("loading-text").textContent = text || "处理中...";
    el.classList.remove("hidden");
}

function hideLoading() {
    document.getElementById("loading").classList.add("hidden");
}

function showError(msg) {
    const el = document.getElementById("error-message");
    el.textContent = msg;
    el.classList.remove("hidden");
}

function hideError() {
    document.getElementById("error-message").classList.add("hidden");
}

document.addEventListener("DOMContentLoaded", init);