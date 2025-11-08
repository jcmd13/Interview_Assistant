"""
Smart Question Classifier
Classifies interview questions into: greeting, technical, or career
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from datetime import datetime


class QuestionType(Enum):
    """Types of questions"""
    GREETING = "greeting"
    TECHNICAL = "technical"
    CAREER = "career"
    UNKNOWN = "unknown"


class QuestionClassifier:
    """Classifies interview questions by type"""

    def __init__(self):
        """Initialize classifier with keyword patterns"""
        self.greeting_patterns = [
            r'\b(hey|hi|hello|how\s+are\s+you|how\s+are\s+things|how\s+do\s+you|how\'s\s+it|what\'s\s+up|welcome|glad|nice\s+to|good\s+morning|good\s+afternoon|good\s+evening|thanks\s+for|appreciate\s+you|looking\s+forward)\b',
            r'\b(doing|going)\s+(well|good|great|okay)\b',
        ]

        self.technical_patterns = [
            # Architecture and design
            r'\b(architecture|design|system\s+design|scalability|latency|throughput|load\s+balancing|caching|database|sql|nosql|api|rest|graphql|microservices|distributed|consensus|replication)\b',
            # DevOps and Infrastructure
            r'\b(kubernetes|docker|container|orchestration|ci\/cd|pipeline|jenkins|gitlab|devops|terraform|ansible|infrastructure\s+as\s+code|iac|deployment|release|rollback|canary)\b',
            # AWS and Cloud
            r'\b(aws|ec2|s3|lambda|rds|dynamodb|cloudformation|autoscaling|elasticache|cloudfront|route53|iam|vpc|security\s+group|cloud|azure|gcp)\b',
            # Security and Compliance
            r'\b(security|encryption|ssl|tls|authentication|authorization|oauth|jwt|mfa|multi\s+factor|penetration|vulnerability|compliance|gdpr|hipaa|pci|threat|attack|malware|firewall)\b',
            # Monitoring and Observability
            r'\b(monitoring|logging|metrics|prometheus|grafana|elk|elasticsearch|datadog|newrelic|observability|trace|span|apm|alert|anomaly)\b',
            # Programming and Languages
            r'\b(python|javascript|typescript|java|golang|rust|c\+\+|algorithm|data\s+structure|optimization|performance|refactor|testing|unittest|pytest|mock)\b',
            # Networking
            r'\b(tcp|udp|http|dns|ip|network|port|protocol|bandwidth|latency|throughput|packet|routing|bgp|ospf)\b',
            # Database
            r'\b(database|query|index|partition|shard|replica|backup|recovery|transaction|acid|consistency|availability|partition\s+tolerance)\b',
        ]

        self.career_patterns = [
            # Goals and aspirations
            r'\b(goal|aspiration|career\s+path|next|growth|opportunity|advance|promotion|lead|leadership|team\s+lead|manager|director|vp|cto|ceo|executive)\b',
            # Learning and Development
            r'\b(learn|learn|improve|skill|strength|weakness|challenge|overcome|development|training|certification|course|mentor|mentorship|feedback)\b',
            # Work style and culture
            r'\b(collaborate|collaboration|teamwork|culture|work\s+environment|work\s+life\s+balance|remote|flexible|prefer|enjoy|passionate|motivated|driven)\b',
            # Experience and background
            r'\b(experience|background|previous|worked|worked\s+with|familiar|expertise|specialization|years\s+of|decade)\b',
            # Motivation and values
            r'\b(motivated|motivate|inspire|inspired|value|ethics|integrity|responsibility|accountability|mission|vision|impact|contribution)\b',
            # Company and role fit
            r'\b(why\s+us|why\s+this|interested|exciting|challenge|role|position|team|company|organization|industry|sector)\b',
        ]

        self.stats = {
            "classified": 0,
            "greeting": 0,
            "technical": 0,
            "career": 0,
            "unknown": 0,
        }

    def classify(self, question: str) -> Dict[str, Any]:
        """
        Classify a question into greeting, technical, or career
        Returns dict with classification result and confidence
        """
        if not question or len(question.strip()) < 3:
            return {
                "type": QuestionType.UNKNOWN.value,
                "confidence": 0.0,
                "reason": "Question too short",
            }

        question_lower = question.lower()

        # Check pattern matches for each category
        greeting_matches = self._count_pattern_matches(question_lower, self.greeting_patterns)
        technical_matches = self._count_pattern_matches(question_lower, self.technical_patterns)
        career_matches = self._count_pattern_matches(question_lower, self.career_patterns)

        total_matches = greeting_matches + technical_matches + career_matches

        # Determine type based on matches
        if total_matches == 0:
            result_type = QuestionType.UNKNOWN
            confidence = 0.0
            reason = "No matching keywords found"
        elif greeting_matches > technical_matches and greeting_matches > career_matches:
            result_type = QuestionType.GREETING
            confidence = greeting_matches / (total_matches + 1)
            reason = f"Greeting keywords detected ({greeting_matches} matches)"
        elif technical_matches > greeting_matches and technical_matches > career_matches:
            result_type = QuestionType.TECHNICAL
            confidence = technical_matches / (total_matches + 1)
            reason = f"Technical keywords detected ({technical_matches} matches)"
        elif career_matches > greeting_matches and career_matches > technical_matches:
            result_type = QuestionType.CAREER
            confidence = career_matches / (total_matches + 1)
            reason = f"Career keywords detected ({career_matches} matches)"
        else:
            # Tie-breaker: use the category with most matches
            max_matches = max(greeting_matches, technical_matches, career_matches)
            if max_matches == greeting_matches:
                result_type = QuestionType.GREETING
            elif max_matches == technical_matches:
                result_type = QuestionType.TECHNICAL
            else:
                result_type = QuestionType.CAREER
            confidence = max_matches / (total_matches + 1)
            reason = f"Determined by match priority ({max_matches} matches)"

        # Update statistics
        self.stats["classified"] += 1
        self.stats[result_type.value] += 1

        return {
            "type": result_type.value,
            "confidence": min(confidence, 1.0),
            "reason": reason,
            "greeting_matches": greeting_matches,
            "technical_matches": technical_matches,
            "career_matches": career_matches,
            "timestamp": datetime.now().isoformat(),
        }

    def _count_pattern_matches(self, text: str, patterns: List[str]) -> int:
        """Count how many patterns match in the text"""
        count = 0
        for pattern in patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                count += len(matches)
            except re.error:
                # Skip invalid regex patterns
                continue
        return count

    def filter_greetings(self, question: str, threshold: float = 0.7) -> bool:
        """
        Check if question is a greeting that should be filtered
        Returns True if question should be filtered (is a greeting)
        """
        result = self.classify(question)
        is_greeting = (
            result["type"] == QuestionType.GREETING.value
            and result["confidence"] >= threshold
        )
        return is_greeting

    def get_stats(self) -> Dict[str, Any]:
        """Get classification statistics"""
        return {
            **self.stats,
            "greeting_pct": (
                self.stats["greeting"] / max(self.stats["classified"], 1) * 100
            ),
            "technical_pct": (
                self.stats["technical"] / max(self.stats["classified"], 1) * 100
            ),
            "career_pct": (
                self.stats["career"] / max(self.stats["classified"], 1) * 100
            ),
            "unknown_pct": (
                self.stats["unknown"] / max(self.stats["classified"], 1) * 100
            ),
        }

    def reset_stats(self):
        """Reset classification statistics"""
        self.stats = {
            "classified": 0,
            "greeting": 0,
            "technical": 0,
            "career": 0,
            "unknown": 0,
        }


# Global classifier instance
_classifier: Optional[QuestionClassifier] = None


def get_classifier() -> QuestionClassifier:
    """Get or create global question classifier"""
    global _classifier
    if _classifier is None:
        _classifier = QuestionClassifier()
    return _classifier
