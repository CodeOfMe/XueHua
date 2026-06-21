"""Photo-based learning module for Xuehua.

Uses multimodal LLM (e.g., qwen3.5:0.8b via Ollama) to identify objects
in photos and generate Chinese character learning content with pinyin,
pronunciation, and example sentences.
"""

from __future__ import annotations

import base64
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    from pypinyin import pinyin as pypinyin_func, Style
    _PYPINYIN_AVAILABLE = True
except ImportError:
    _PYPINYIN_AVAILABLE = False

logger = logging.getLogger(__name__)

IDENTIFY_PROMPT = """你是一个专业的物品识别和中文启蒙教育助手。请仔细观察这张图片，完成以下任务：

1. 识别图片中的主要物品/场景（用中文名称）
2. 为每个识别到的物品提供：
   - 中文名称
   - 拼音（带声调符号，如 māo）
   - 部首和笔画数
   - 简单的中文解释（适合3-6岁儿童理解）
   - 一个简单的造句示例
   - 该物品的英文对应词

请用JSON格式回复，格式如下：
```json
{
  "items": [
    {
      "name": "猫",
      "pinyin": "māo",
      "radical": "犭",
      "strokes": 11,
      "explanation": "猫是一种毛茸茸的小动物，会喵喵叫，喜欢抓老鼠。",
      "example": "我家有一只可爱的小猫。",
      "example_pinyin": "wǒ jiā yǒu yī zhī kě ài de xiǎo māo。",
      "english": "cat"
    }
  ],
  "scene_description": "简短描述图片场景"
}
```

注意：
- 只识别图片中清晰可见的物品
- 拼音必须带声调
- 解释要简单易懂，适合幼儿
- 如果图片模糊或无法识别，返回空items数组"""

LEARN_PROMPT = """你是一个专业的中文启蒙教育助手。基于图片中识别到的物品，请生成适合3-6岁儿童的学习内容。

识别到的物品：{items}

请生成以下内容，用JSON格式回复：
```json
{
  "lesson": {{
    "title": "课程标题",
    "words": [
      {{
        "word": "猫",
        "pinyin": "māo",
        "radical": "犭",
        "strokes": 11,
        "meaning": "一种毛茸茸的小动物",
        "example_sentence": "小猫在睡觉。",
        "example_pinyin": "xiǎo māo zài shuì jiào。",
        "example_translation": "The kitten is sleeping.",
        "stroke_order_hint": "从左到右，先写犭再写苗",
        "fun_fact": "猫一天要睡16个小时！",
        "related_words": ["小猫", "猫咪", "猫粮"]
      }}
    ],
    "chant": "小猫小猫喵喵叫，毛茸茸的真可爱",
    "story": "从前有一只小猫，它最喜欢在太阳下睡觉...",
    "questions": [
      "你能在家里找到猫吗？",
      "猫是怎么叫的？"
    ]
  }
}
```

注意：
- 拼音必须带声调符号
- 内容要生动有趣，适合3-6岁儿童
- 故事要简短（50字以内）
- 儿歌要朗朗上口"""


@dataclass
class PhotoItem:
    name: str = ""
    pinyin: str = ""
    radical: str = ""
    strokes: int = 0
    explanation: str = ""
    example: str = ""
    example_pinyin: str = ""
    english: str = ""


@dataclass
class LearnWord:
    word: str = ""
    pinyin: str = ""
    radical: str = ""
    strokes: int = 0
    meaning: str = ""
    example_sentence: str = ""
    example_pinyin: str = ""
    example_translation: str = ""
    stroke_order_hint: str = ""
    fun_fact: str = ""
    related_words: List[str] = field(default_factory=list)


@dataclass
class PhotoLesson:
    title: str = ""
    words: List[LearnWord] = field(default_factory=list)
    chant: str = ""
    story: str = ""
    questions: List[str] = field(default_factory=list)


@dataclass
class IdentifyResult:
    items: List[PhotoItem] = field(default_factory=list)
    scene_description: str = ""
    raw_response: str = ""


def get_pinyin(text: str, tone: bool = True) -> str:
    if _PYPINYIN_AVAILABLE:
        style = Style.TONE if tone else Style.NORMAL
        result = pypinyin_func(text, style=style, heteronym=False)
        return " ".join([p[0] for p in result])
    return _simple_pinyin(text)


def _simple_pinyin(text: str) -> str:
    PINYIN_MAP = {
        "一": "yī", "二": "èr", "三": "sān", "四": "sì", "五": "wǔ",
        "六": "liù", "七": "qī", "八": "bā", "九": "jiǔ", "十": "shí",
        "人": "rén", "大": "dà", "小": "xiǎo", "中": "zhōng", "上": "shàng",
        "下": "xià", "日": "rì", "月": "yuè", "水": "shuǐ", "火": "huǒ",
        "山": "shān", "石": "shí", "田": "tián", "土": "tǔ", "木": "mù",
        "猫": "māo", "狗": "gǒu", "鸟": "niǎo", "鱼": "yú", "花": "huā",
        "草": "cǎo", "树": "shù", "车": "chē", "门": "mén", "书": "shū",
        "手": "shǒu", "口": "kǒu", "耳": "ěr", "目": "mù", "足": "zú",
        "天": "tiān", "地": "dì", "风": "fēng", "雨": "yǔ", "云": "yún",
        "马": "mǎ", "牛": "niú", "羊": "yáng", "虫": "chóng", "果": "guǒ",
        "米": "mǐ", "竹": "zhú", "毛": "máo", "皮": "pí", "肉": "ròu",
    }
    result = []
    for ch in text:
        if ch in PINYIN_MAP:
            result.append(PINYIN_MAP[ch])
        else:
            result.append(ch)
    return " ".join(result)


def _extract_json(text: str) -> Optional[Dict]:
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def identify_photo(
    image_data: str,
    ollama_client,
    model: str = "",
) -> IdentifyResult:
    result = IdentifyResult()
    if not image_data:
        return result

    if not model:
        vision_models = ollama_client.get_vision_models()
        if vision_models:
            model = vision_models[0]
        else:
            chat_models = ollama_client.get_chat_models()
            if chat_models:
                model = chat_models[0]
            else:
                result.raw_response = "Error: No model available"
                return result

    logger.info("[PhotoLearn] Identifying with model: %s", model)
    response = ollama_client.chat_vision(IDENTIFY_PROMPT, image_data, model)
    result.raw_response = response

    if not response:
        return result

    data = _extract_json(response)
    if not data:
        return result

    result.scene_description = data.get("scene_description", "")
    for item_data in data.get("items", []):
        item = PhotoItem(
            name=item_data.get("name", ""),
            pinyin=item_data.get("pinyin", ""),
            radical=item_data.get("radical", ""),
            strokes=item_data.get("strokes", 0),
            explanation=item_data.get("explanation", ""),
            example=item_data.get("example", ""),
            example_pinyin=item_data.get("example_pinyin", ""),
            english=item_data.get("english", ""),
        )
        if item.name:
            if not item.pinyin:
                item.pinyin = get_pinyin(item.name)
            result.items.append(item)

    return result


def generate_lesson(
    items: List[PhotoItem],
    ollama_client,
    model: str = "",
) -> PhotoLesson:
    lesson = PhotoLesson()
    if not items:
        return lesson

    if ollama_client is None:
        return lesson

    if not model:
        vision_models = ollama_client.get_vision_models()
        if vision_models:
            model = vision_models[0]
        else:
            chat_models = ollama_client.get_chat_models()
            if chat_models:
                model = chat_models[0]
            else:
                return lesson

    items_desc = "\n".join([
        f"- {item.name}({item.pinyin}): {item.explanation}"
        for item in items
    ])
    prompt = LEARN_PROMPT.format(items=items_desc)

    logger.info("[PhotoLearn] Generating lesson with model: %s", model)
    messages = [{"role": "user", "content": prompt}]
    response = ollama_client.chat_complete(messages, model, temperature=0.7)

    if not response:
        return lesson

    data = _extract_json(response)
    if not data:
        return lesson

    lesson_data = data.get("lesson", data)
    lesson.title = lesson_data.get("title", "")
    lesson.chant = lesson_data.get("chant", "")
    lesson.story = lesson_data.get("story", "")
    lesson.questions = lesson_data.get("questions", [])

    for word_data in lesson_data.get("words", []):
        word = LearnWord(
            word=word_data.get("word", ""),
            pinyin=word_data.get("pinyin", ""),
            radical=word_data.get("radical", ""),
            strokes=word_data.get("strokes", 0),
            meaning=word_data.get("meaning", ""),
            example_sentence=word_data.get("example_sentence", ""),
            example_pinyin=word_data.get("example_pinyin", ""),
            example_translation=word_data.get("example_translation", ""),
            stroke_order_hint=word_data.get("stroke_order_hint", ""),
            fun_fact=word_data.get("fun_fact", ""),
            related_words=word_data.get("related_words", []),
        )
        if word.word:
            if not word.pinyin:
                word.pinyin = get_pinyin(word.word)
            lesson.words.append(word)

    return lesson


def encode_image_file(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")