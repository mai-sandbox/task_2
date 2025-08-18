from dataclasses import dataclass, field
from typing import Any, Optional, Annotated, List, Dict
import operator

from pydantic import BaseModel, Field

class Person(BaseModel):
    """A class representing a person to research."""

    name: Optional[str] = None
    """The name of the person."""
    company: Optional[str] = None
    """The current company of the person."""
    linkedin: Optional[str] = None
    """The Linkedin URL of the person."""
    email: str
    """The email of the person."""
    role: Optional[str] = None
    """The current title of the person."""


class ReflectionResult(BaseModel):
    """Structured output from the reflection step."""
    
    years_experience: Optional[int] = Field(None, description="Total years of professional experience")
    current_company: Optional[str] = Field(None, description="Current company where the person works")
    current_role: Optional[str] = Field(None, description="Current job title or role")
    prior_companies: List[str] = Field(default_factory=list, description="List of previous companies the person has worked at")
    completeness_score: float = Field(0.0, description="Score from 0-1 indicating how complete the research is")
    needs_more_research: bool = Field(True, description="Whether more research is needed to gather complete information")
    reasoning: str = Field("", description="Explanation of what information is missing or why research is complete")


@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OverallState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"


