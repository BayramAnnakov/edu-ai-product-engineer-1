"""
Shared Data Types and Configurations

This module contains shared data structures and configurations used across the project.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FeatureProposal:
    """Represents a proposed feature with ID and description."""
    id: int
    description: str

    def md(self) -> str:
        """Returns markdown representation of the feature."""
        return f"{self.id}. {self.description}"


@dataclass
class Persona:
    """Represents a user persona with background and characteristics."""
    name: str
    background: str
    quote: str
    sentiment: str
    pain_points: List[str]
    inspired_by_cluster_id: Optional[str] = None

    @property
    def system_prompt(self) -> str:
        """Generates system prompt for the LLM agent representing this persona."""
        pain_str = "; ".join(self.pain_points)
        return (
            f"You are {self.name}. Act and respond authentically based on this profile:\n"
            f"- Background: {self.background}\n"
            f"- Overall Sentiment towards Spotify: {self.sentiment}\n"
            f"- Key Pain Points/Frustrations: {pain_str}\n"
            f"Always speak in the first person ('I', 'me', 'my'). Keep your responses concise (1-3 sentences unless asked otherwise) and focused on the discussion topic. "
            f"Ground your opinions in your background and pain points. Be honest and natural."
        )

    def md(self) -> str:
        """Returns markdown representation of the persona."""
        pain_str = "\n  - ".join(self.pain_points)
        return (
            f"### {self.name}\n\n"
            f"*{self.quote}*\n\n"
            f"**Background**: {self.background}\n\n"
            f"**Sentiment**: {self.sentiment.capitalize()}\n\n"
            f"**Key Pain Points**:\n  - {pain_str}\n"
        ) 