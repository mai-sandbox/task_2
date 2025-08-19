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
    """Overall state that maintains all information throughout the research workflow."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_of_experience": "Total years of professional work experience",
        "current_company": "Current employer/company name",
        "current_role": "Current job title/position",
        "prior_companies": "List of previous companies worked at with roles and duration"
    })
    "Schema defining what information to extract about the person"

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"

    # Reflection-related fields
    reflection_result: Optional[dict[str, Any]] = field(default=None)
    "Structured output from reflection step containing extracted information"

    needs_more_research: bool = field(default=True)
    "Whether additional research is needed based on reflection analysis"

    reflection_reasoning: Optional[str] = field(default=None)
    "Reasoning for whether to continue research or not"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines the structured information returned to the user."""

    years_of_experience: Optional[int] = field(default=None)
    "Total years of professional work experience"

    current_company: Optional[str] = field(default=None)
    "Current employer/company name"

    current_role: Optional[str] = field(default=None)
    "Current job title/position"

    prior_companies: Optional[list[dict[str, Any]]] = field(default=None)
    "List of previous companies with details like company name, role, and duration"

    research_summary: Optional[str] = field(default=None)
    "Summary of the research findings"

    confidence_score: Optional[float] = field(default=None)
    "Confidence score (0-1) indicating how complete the information is"

    missing_information: Optional[list[str]] = field(default=None)
    "List of information that could not be found or needs verification"



