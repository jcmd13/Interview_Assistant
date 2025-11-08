"""
UI Plugin System for Interview Assistant

Provides modular, pluggable UI components that can be dynamically loaded
and rearranged at runtime. Cards can be swapped, repositioned, and layouts
can be changed without server restart.

Architecture:
- UICard base class: All UI components inherit from this
- Cards: Transcript, Answer Detail, Q&A List, Status, Settings
- Layouts: Interview Stealth, Phone Call, Business Meeting, etc.
- DynamicLayout manager: Coordinates cards and layout changes

All cards communicate via WebSocket with the server.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

from src.core.logger import get_logger

logger = get_logger("system.ui")


class CardType(Enum):
    """Types of UI cards available"""
    TRANSCRIPT = "transcript"
    ANSWER_DETAIL = "answer_detail"
    QA_LIST = "qa_list"
    STATUS = "status"
    SETTINGS = "settings"
    METRICS = "metrics"
    PLUGINS = "plugins"


@dataclass
class CardPosition:
    """Position of a card in grid layout"""
    x: int  # Column (0-based)
    y: int  # Row (0-based)
    width: int = 1  # Width in grid units (default 1)
    height: int = 1  # Height in grid units (default 1)


@dataclass
class UICard:
    """Base class for UI card components"""
    card_id: str
    card_type: CardType
    title: str
    position: CardPosition
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert card to dictionary for serialization"""
        return {
            "card_id": self.card_id,
            "card_type": self.card_type.value,
            "title": self.title,
            "position": {
                "x": self.position.x,
                "y": self.position.y,
                "width": self.position.width,
                "height": self.position.height,
            },
            "enabled": self.enabled,
            "config": self.config,
        }


class UILayout:
    """Defines a layout preset with card arrangement"""

    def __init__(self, name: str, description: str, cards: List[UICard]):
        self.name = name
        self.description = description
        self.cards = cards

    def to_dict(self) -> Dict[str, Any]:
        """Convert layout to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "cards": [card.to_dict() for card in self.cards],
        }


# Layout Presets
LAYOUT_INTERVIEW_STEALTH = UILayout(
    name="Interview Stealth",
    description="Minimal, compact layout for subtle monitoring during interviews",
    cards=[
        UICard(
            card_id="transcript",
            card_type=CardType.TRANSCRIPT,
            title="Transcript",
            position=CardPosition(x=0, y=0, width=2, height=2),
        ),
        UICard(
            card_id="answer",
            card_type=CardType.ANSWER_DETAIL,
            title="Answer",
            position=CardPosition(x=2, y=0, width=1, height=2),
        ),
        UICard(
            card_id="status",
            card_type=CardType.STATUS,
            title="Status",
            position=CardPosition(x=0, y=2, width=3, height=1),
        ),
    ],
)

LAYOUT_PHONE_CALL = UILayout(
    name="Phone Call",
    description="Answer-focused layout for phone screen interviews",
    cards=[
        UICard(
            card_id="answer",
            card_type=CardType.ANSWER_DETAIL,
            title="Answer",
            position=CardPosition(x=0, y=0, width=2, height=2),
        ),
        UICard(
            card_id="transcript",
            card_type=CardType.TRANSCRIPT,
            title="Transcript",
            position=CardPosition(x=2, y=0, width=1, height=2),
        ),
        UICard(
            card_id="qa_list",
            card_type=CardType.QA_LIST,
            title="Q&A",
            position=CardPosition(x=0, y=2, width=3, height=1),
        ),
    ],
)

LAYOUT_BUSINESS_MEETING = UILayout(
    name="Business Meeting",
    description="Balanced layout with equal focus on all elements",
    cards=[
        UICard(
            card_id="transcript",
            card_type=CardType.TRANSCRIPT,
            title="Transcript",
            position=CardPosition(x=0, y=0, width=1, height=2),
        ),
        UICard(
            card_id="answer",
            card_type=CardType.ANSWER_DETAIL,
            title="Answer",
            position=CardPosition(x=1, y=0, width=1, height=2),
        ),
        UICard(
            card_id="qa_list",
            card_type=CardType.QA_LIST,
            title="Q&A History",
            position=CardPosition(x=2, y=0, width=1, height=2),
        ),
        UICard(
            card_id="status",
            card_type=CardType.STATUS,
            title="Status",
            position=CardPosition(x=0, y=2, width=3, height=1),
        ),
    ],
)

# All available layouts
AVAILABLE_LAYOUTS = {
    "interview_stealth": LAYOUT_INTERVIEW_STEALTH,
    "phone_call": LAYOUT_PHONE_CALL,
    "business_meeting": LAYOUT_BUSINESS_MEETING,
}


class DynamicLayoutManager:
    """Manages dynamic UI layout and card arrangement"""

    def __init__(self):
        self.current_layout = LAYOUT_INTERVIEW_STEALTH
        self.cards: Dict[str, UICard] = {card.card_id: card for card in self.current_layout.cards}
        self.on_layout_change: Optional[Callable] = None

    def get_layout(self) -> UILayout:
        """Get current layout"""
        return self.current_layout

    def set_layout(self, layout_name: str) -> bool:
        """Change to different layout preset"""
        if layout_name not in AVAILABLE_LAYOUTS:
            logger.warning("invalid_layout", name=layout_name)
            return False

        try:
            layout = AVAILABLE_LAYOUTS[layout_name]
            self.current_layout = layout
            self.cards = {card.card_id: card for card in layout.cards}

            logger.info("layout_changed", name=layout_name)

            if self.on_layout_change:
                self.on_layout_change(layout)

            return True
        except Exception as e:
            logger.error("set_layout_failed", error=str(e))
            return False

    def update_card_position(self, card_id: str, position: CardPosition) -> bool:
        """Update position of a card"""
        if card_id not in self.cards:
            logger.warning("card_not_found", card_id=card_id)
            return False

        try:
            self.cards[card_id].position = position
            logger.info("card_position_updated", card_id=card_id)
            return True
        except Exception as e:
            logger.error("update_position_failed", error=str(e))
            return False

    def toggle_card(self, card_id: str) -> bool:
        """Toggle card visibility"""
        if card_id not in self.cards:
            return False

        try:
            self.cards[card_id].enabled = not self.cards[card_id].enabled
            logger.info("card_toggled", card_id=card_id, enabled=self.cards[card_id].enabled)
            return True
        except Exception as e:
            logger.error("toggle_card_failed", error=str(e))
            return False

    def get_cards_for_layout(self) -> List[UICard]:
        """Get all cards in current layout"""
        return list(self.cards.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert current layout to dictionary"""
        return {
            "layout_name": self.current_layout.name,
            "layout_description": self.current_layout.description,
            "cards": [card.to_dict() for card in self.get_cards_for_layout()],
        }


# Global layout manager instance
_layout_manager: Optional[DynamicLayoutManager] = None


def get_layout_manager() -> DynamicLayoutManager:
    """Get or create global layout manager"""
    global _layout_manager
    if _layout_manager is None:
        _layout_manager = DynamicLayoutManager()
        logger.info("layout_manager_initialized")
    return _layout_manager


def get_available_layouts() -> Dict[str, Dict[str, str]]:
    """Get list of available layouts"""
    return {
        name: {
            "name": layout.name,
            "description": layout.description,
        }
        for name, layout in AVAILABLE_LAYOUTS.items()
    }
