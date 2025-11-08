"""
Answer Persistence Manager
Handles pinning/dismissing answers and tracking answer state
"""

import json
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from pathlib import Path


class AnswerState(Enum):
    """State of an answer"""
    ACTIVE = "active"
    PINNED = "pinned"
    DISMISSED = "dismissed"
    ARCHIVED = "archived"


class PersistentAnswer:
    """Represents a persistent answer with state tracking"""

    def __init__(self, answer_id: str, question: str, answer_text: str):
        """Initialize answer"""
        self.answer_id = answer_id
        self.question = question
        self.answer_text = answer_text
        self.state = AnswerState.ACTIVE
        self.created_at = datetime.now().isoformat()
        self.pinned_at: Optional[str] = None
        self.dismissed_at: Optional[str] = None
        self.notes: str = ""
        self.tags: List[str] = []

    def pin(self):
        """Pin this answer"""
        self.state = AnswerState.PINNED
        self.pinned_at = datetime.now().isoformat()

    def unpin(self):
        """Unpin this answer"""
        self.state = AnswerState.ACTIVE
        self.pinned_at = None

    def dismiss(self):
        """Dismiss this answer"""
        self.state = AnswerState.DISMISSED
        self.dismissed_at = datetime.now().isoformat()

    def restore(self):
        """Restore a dismissed answer"""
        self.state = AnswerState.ACTIVE
        self.dismissed_at = None

    def add_tag(self, tag: str):
        """Add a tag to the answer"""
        if tag not in self.tags:
            self.tags.append(tag)

    def add_note(self, note: str):
        """Add or update notes on the answer"""
        self.notes = note

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "answer_id": self.answer_id,
            "question": self.question,
            "answer_text": self.answer_text,
            "state": self.state.value,
            "created_at": self.created_at,
            "pinned_at": self.pinned_at,
            "dismissed_at": self.dismissed_at,
            "notes": self.notes,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PersistentAnswer":
        """Create from dictionary"""
        answer = PersistentAnswer(
            data["answer_id"],
            data["question"],
            data["answer_text"]
        )
        answer.state = AnswerState(data.get("state", "active"))
        answer.created_at = data.get("created_at", datetime.now().isoformat())
        answer.pinned_at = data.get("pinned_at")
        answer.dismissed_at = data.get("dismissed_at")
        answer.notes = data.get("notes", "")
        answer.tags = data.get("tags", [])
        return answer


class AnswerPersistenceManager:
    """Manages answer persistence and state"""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize answer persistence manager"""
        self.answers: Dict[str, PersistentAnswer] = {}
        self.storage_path = storage_path or Path.home() / ".interview-assistant" / "answers.json"
        self.load_answers()

    def add_answer(self, answer_id: str, question: str, answer_text: str) -> PersistentAnswer:
        """Add a new answer"""
        answer = PersistentAnswer(answer_id, question, answer_text)
        self.answers[answer_id] = answer
        self.save_answers()
        return answer

    def get_answer(self, answer_id: str) -> Optional[PersistentAnswer]:
        """Get an answer by ID"""
        return self.answers.get(answer_id)

    def pin_answer(self, answer_id: str) -> bool:
        """Pin an answer"""
        answer = self.get_answer(answer_id)
        if answer:
            answer.pin()
            self.save_answers()
            return True
        return False

    def unpin_answer(self, answer_id: str) -> bool:
        """Unpin an answer"""
        answer = self.get_answer(answer_id)
        if answer:
            answer.unpin()
            self.save_answers()
            return True
        return False

    def dismiss_answer(self, answer_id: str) -> bool:
        """Dismiss an answer"""
        answer = self.get_answer(answer_id)
        if answer:
            answer.dismiss()
            self.save_answers()
            return True
        return False

    def restore_answer(self, answer_id: str) -> bool:
        """Restore a dismissed answer"""
        answer = self.get_answer(answer_id)
        if answer:
            answer.restore()
            self.save_answers()
            return True
        return False

    def add_tag_to_answer(self, answer_id: str, tag: str) -> bool:
        """Add a tag to an answer"""
        answer = self.get_answer(answer_id)
        if answer:
            answer.add_tag(tag)
            self.save_answers()
            return True
        return False

    def add_note_to_answer(self, answer_id: str, note: str) -> bool:
        """Add a note to an answer"""
        answer = self.get_answer(answer_id)
        if answer:
            answer.add_note(note)
            self.save_answers()
            return True
        return False

    def get_pinned_answers(self) -> List[PersistentAnswer]:
        """Get all pinned answers"""
        return [a for a in self.answers.values() if a.state == AnswerState.PINNED]

    def get_active_answers(self) -> List[PersistentAnswer]:
        """Get all active answers"""
        return [a for a in self.answers.values() if a.state == AnswerState.ACTIVE]

    def get_dismissed_answers(self) -> List[PersistentAnswer]:
        """Get all dismissed answers"""
        return [a for a in self.answers.values() if a.state == AnswerState.DISMISSED]

    def get_answers_by_tag(self, tag: str) -> List[PersistentAnswer]:
        """Get answers with a specific tag"""
        return [a for a in self.answers.values() if tag in a.tags]

    def get_status(self) -> Dict[str, Any]:
        """Get status and statistics"""
        return {
            "total_answers": len(self.answers),
            "pinned_count": len(self.get_pinned_answers()),
            "active_count": len(self.get_active_answers()),
            "dismissed_count": len(self.get_dismissed_answers()),
            "unique_tags": list(set(tag for a in self.answers.values() for tag in a.tags)),
        }

    def save_answers(self):
        """Save answers to storage"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                answer_id: answer.to_dict()
                for answer_id, answer in self.answers.items()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving answers: {e}")

    def load_answers(self):
        """Load answers from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.answers = {
                        answer_id: PersistentAnswer.from_dict(answer_data)
                        for answer_id, answer_data in data.items()
                    }
        except Exception as e:
            print(f"Error loading answers: {e}")
            self.answers = {}

    def clear_dismissed(self):
        """Clear all dismissed answers"""
        self.answers = {
            aid: a for aid, a in self.answers.items()
            if a.state != AnswerState.DISMISSED
        }
        self.save_answers()

    def export_pinned_answers(self, format: str = "markdown") -> str:
        """Export pinned answers"""
        pinned = self.get_pinned_answers()

        if format == "markdown":
            lines = ["# Pinned Answers\n"]
            for answer in pinned:
                lines.append(f"## Q: {answer.question}\n")
                lines.append(f"{answer.answer_text}\n")
                if answer.notes:
                    lines.append(f"**Notes:** {answer.notes}\n")
                if answer.tags:
                    lines.append(f"**Tags:** {', '.join(answer.tags)}\n")
                lines.append("\n---\n\n")
            return "".join(lines)

        elif format == "json":
            return json.dumps(
                [a.to_dict() for a in pinned],
                indent=2
            )

        return ""


# Global persistence manager instance
_persistence_manager: Optional[AnswerPersistenceManager] = None


def get_persistence_manager() -> AnswerPersistenceManager:
    """Get or create global answer persistence manager"""
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = AnswerPersistenceManager()
    return _persistence_manager
