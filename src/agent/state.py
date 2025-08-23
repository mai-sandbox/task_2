import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, Optional

from pydantic import BaseModel


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

    extraction_schema: dict[str, Any] = field(
        default_factory=lambda: {
            "years_of_experience": "Number of years of professional work experience",
            "current_company": "Current company or organization the person works for",
            "current_role": "Current job title or position",
            "prior_companies": "List of previous companies or organizations worked at with roles and timeframes",
        }
    )
    "Schema defining the structured information to extract about the person"

    # Reflection state fields
    structured_research_results: Optional[dict[str, Any]] = field(default=None)
    "Structured extraction of research findings based on the schema"

    research_satisfaction_assessment: Optional[dict[str, Any]] = field(default=None)
    "Assessment of research completeness and decision on whether to continue"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines the final structured results returned by the graph."""

    person: Person
    "The person that was researched"

    structured_research_results: dict[str, Any]
    "Structured extraction of research findings including years of experience, current company, role, and prior companies"

    research_satisfaction_assessment: dict[str, Any]
    "Assessment of research completeness including satisfaction level, missing information, and reasoning"

    completed_notes: list[str]
    "All research notes collected during the process"
