"""Learning module for Xuehua - progressive lessons, SRS, and exercises."""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import Config, PROGRESS_DIR
from .japanese import (
    Token,
    add_furigana,
    annotate_text,
    detect_japanese_level,
    kana_to_romaji,
    tokenize,
)

PROGRESS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SRSCard:
    """A spaced repetition card."""
    card_id: str
    front: str
    back: str
    reading: str = ""
    level: str = "N5"
    category: str = ""
    easiness: float = 2.5
    interval: int = 0
    repetitions: int = 0
    next_review: float = 0.0
    last_review: float = 0.0

    def to_dict(self) -> dict:
        return {
            "card_id": self.card_id,
            "front": self.front,
            "back": self.back,
            "reading": self.reading,
            "level": self.level,
            "category": self.category,
            "easiness": self.easiness,
            "interval": self.interval,
            "repetitions": self.repetitions,
            "next_review": self.next_review,
            "last_review": self.last_review,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SRSCard":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Lesson:
    """A single lesson with vocabulary, grammar, and exercises."""
    lesson_id: str
    title: str
    level: str
    description: str = ""
    vocabulary: List[Dict] = field(default_factory=list)
    grammar_points: List[Dict] = field(default_factory=list)
    example_sentences: List[Dict] = field(default_factory=list)
    exercises: List[Dict] = field(default_factory=list)
    order: int = 0

    def to_dict(self) -> dict:
        return {
            "lesson_id": self.lesson_id,
            "title": self.title,
            "level": self.level,
            "description": self.description,
            "vocabulary": self.vocabulary,
            "grammar_points": self.grammar_points,
            "example_sentences": self.example_sentences,
            "exercises": self.exercises,
            "order": self.order,
        }


@dataclass
class ExerciseResult:
    """Result of completing an exercise."""
    exercise_id: str
    correct: bool
    user_answer: str
    correct_answer: str
    time_taken: float = 0.0


class SRSManager:
    """Spaced repetition manager using SM-2 algorithm."""

    def __init__(self, progress_file: Path = None):
        self.progress_file = progress_file or PROGRESS_DIR / "srs_cards.json"
        self.cards: Dict[str, SRSCard] = {}
        self._load()

    def _load(self):
        if self.progress_file.exists():
            try:
                data = json.loads(self.progress_file.read_text(encoding="utf-8"))
                for card_data in data.get("cards", []):
                    card = SRSCard.from_dict(card_data)
                    self.cards[card.card_id] = card
            except (json.JSONDecodeError, TypeError):
                self.cards = {}

    def _save(self):
        data = {
            "cards": [c.to_dict() for c in self.cards.values()],
        }
        self.progress_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add_card(self, card: SRSCard):
        self.cards[card.card_id] = card
        self._save()

    def review_card(self, card_id: str, quality: int) -> Optional[SRSCard]:
        """Review a card with quality rating (0-5).

        0 = complete blackout, 5 = perfect recall.
        Uses SM-2 algorithm.
        """
        card = self.cards.get(card_id)
        if card is None:
            return None

        if quality < 3:
            card.repetitions = 0
            card.interval = 1
            card.easiness = max(1.3, card.easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        else:
            if card.repetitions == 0:
                card.interval = 1
            elif card.repetitions == 1:
                card.interval = 6
            else:
                card.interval = round(card.interval * card.easiness)

            card.repetitions += 1
            card.easiness = max(1.3, card.easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

        card.last_review = time.time()
        card.next_review = card.last_review + card.interval * 86400
        self._save()
        return card

    def get_due_cards(self, limit: int = 20, level: str = "") -> List[SRSCard]:
        """Get cards due for review."""
        now = time.time()
        due = []
        for card in self.cards.values():
            if card.next_review <= now:
                if level and card.level != level:
                    continue
                due.append(card)
        due.sort(key=lambda c: c.next_review)
        return due[:limit]

    def get_stats(self) -> Dict:
        """Get SRS statistics."""
        now = time.time()
        total = len(self.cards)
        due = sum(1 for c in self.cards.values() if c.next_review <= now)
        learned = sum(1 for c in self.cards.values() if c.repetitions >= 3)
        by_level = {}
        for card in self.cards.values():
            by_level.setdefault(card.level, 0)
            by_level[card.level] += 1
        return {
            "total": total,
            "due": due,
            "learned": learned,
            "by_level": by_level,
        }


class ProgressTracker:
    """Track user learning progress."""

    def __init__(self, progress_file: Path = None):
        self.progress_file = progress_file or PROGRESS_DIR / "progress.json"
        self.data: Dict = {
            "lessons_completed": [],
            "vocabulary_learned": {},
            "grammar_learned": {},
            "total_study_time": 0,
            "current_level": "N5",
            "streak_days": 0,
            "last_study_date": "",
            "kanji_learned": [],
            "exercise_history": [],
        }
        self._load()

    def _load(self):
        if self.progress_file.exists():
            try:
                saved = json.loads(self.progress_file.read_text(encoding="utf-8"))
                self.data.update(saved)
            except (json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        self.progress_file.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def complete_lesson(self, lesson_id: str):
        if lesson_id not in self.data["lessons_completed"]:
            self.data["lessons_completed"].append(lesson_id)
        self._save()

    def learn_vocabulary(self, word: str, meaning: str, level: str = "N5"):
        self.data["vocabulary_learned"][word] = {
            "meaning": meaning,
            "level": level,
            "learned_at": time.time(),
        }
        self._save()

    def learn_kanji(self, kanji: str):
        if kanji not in self.data["kanji_learned"]:
            self.data["kanji_learned"].append(kanji)
        self._save()

    def get_learned_kanji_set(self) -> set:
        return set(self.data.get("kanji_learned", []))

    def get_current_level(self) -> str:
        return self.data.get("current_level", "N5")

    def set_current_level(self, level: str):
        self.data["current_level"] = level
        self._save()

    def get_progress_summary(self) -> Dict:
        return {
            "lessons_completed": len(self.data["lessons_completed"]),
            "vocabulary_count": len(self.data["vocabulary_learned"]),
            "kanji_count": len(self.data.get("kanji_learned", [])),
            "current_level": self.data.get("current_level", "N5"),
            "streak_days": self.data.get("streak_days", 0),
            "total_study_time": self.data.get("total_study_time", 0),
        }


class ExerciseGenerator:
    """Generate exercises for language learning."""

    def __init__(self, config: Config, progress: ProgressTracker, srs: SRSManager):
        self.config = config
        self.progress = progress
        self.srs = srs

    def generate_multiple_choice(
        self, items: List[Dict], num_choices: int = 4
    ) -> List[Dict]:
        """Generate multiple choice exercises from vocabulary items.

        Each item should have: word, meaning, reading
        """
        if len(items) < 2:
            return []

        exercises = []
        for item in items:
            choices = [item["meaning"]]
            others = [i for i in items if i["meaning"] != item["meaning"]]
            if len(others) >= num_choices - 1:
                distractors = random.sample(others, num_choices - 1)
            else:
                distractors = others

            for d in distractors:
                choices.append(d["meaning"])

            random.shuffle(choices)
            correct_index = choices.index(item["meaning"])

            learned_kanji = self.progress.get_learned_kanji_set()
            annotated = annotate_text(
                item["word"],
                show_furigana=self.config.show_furigana,
                show_romaji=self.config.romaji_enabled,
                learned_kanji=learned_kanji,
            )

            exercises.append({
                "type": "multiple_choice",
                "question": f"「{annotated.html_ruby}」的读音是？" if not self.config.romaji_enabled else f"What does 「{annotated.html_ruby}」mean?",
                "choices": choices,
                "correct_index": correct_index,
                "word": item["word"],
                "meaning": item["meaning"],
                "reading": item.get("reading", ""),
                "level": item.get("level", "N5"),
            })

        return exercises

    def generate_fill_blank(
        self, sentences: List[Dict], learned_kanji: Optional[set] = None
    ) -> List[Dict]:
        """Generate fill-in-the-blank exercises from example sentences.

        Each sentence should have: japanese, translation, vocabulary
        """
        if learned_kanji is None:
            learned_kanji = set()

        exercises = []
        for sent in sentences:
            jp = sent["japanese"]
            annotated = annotate_text(
                jp,
                show_furigana=True,
                show_romaji=self.config.romaji_enabled,
                learned_kanji=learned_kanji,
            )

            exercises.append({
                "type": "fill_blank",
                "sentence": annotated.html_ruby,
                "sentence_plain": jp,
                "reading": annotated.plain_reading,
                "romaji": annotated.html_romaji,
                "translation": sent.get("translation", ""),
                "level": sent.get("level", "N5"),
            })

        return exercises

    def generate_reading_quiz(
        self, vocabulary: List[Dict], learned_kanji: Optional[set] = None
    ) -> List[Dict]:
        """Generate reading comprehension quizzes.

        Each vocabulary item should have: word, reading, meaning
        """
        if learned_kanji is None:
            learned_kanji = set()

        exercises = []
        for item in vocabulary:
            annotated = annotate_text(
                item["word"],
                show_furigana=False,
                show_romaji=False,
                learned_kanji=learned_kanji,
            )

            choices = [item["reading"]]
            others = [i for i in vocabulary if i.get("reading") != item["reading"]]
            if len(others) >= 3:
                for other in random.sample(others, 3):
                    choices.append(other["reading"])
            else:
                choices.extend([o["reading"] for o in others])

            random.shuffle(choices)
            correct_index = choices.index(item["reading"])

            exercises.append({
                "type": "reading_quiz",
                "question": f"「{annotated.html_ruby}」的正确读音是？",
                "choices": choices,
                "correct_index": correct_index,
                "word": item["word"],
                "reading": item["reading"],
                "meaning": item.get("meaning", ""),
                "level": item.get("level", "N5"),
            })

        return exercises