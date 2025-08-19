"""State definitions for the people researcher agent."""

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
    
    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_of_experience": "Number of years of professional work experience",
        "current_company": "Name of current employer/company",
        "current_role": "Current job title/position",
        "prior_companies": "List of previous companies worked at with roles and durations",
        "education": "Educational background including degrees and institutions",
        "skills": "Key professional skills and competencies",
        "achievements": "Notable accomplishments and recognitions"
    })
    "Schema defining what information to extract about the person"
    
    reflection_result: dict[str, Any] = field(default=None)
    "Result of reflection step including structured data and assessment"
    
    needs_more_research: bool = field(default=False)
    "Whether additional research is needed based on reflection"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines what gets returned to the user."""
    
    reflection_result: dict[str, Any]
    "Structured information about the person with assessment"
    
    completed_notes: list[str] = field(default_factory=list)
    "Raw notes from research"
    
    needs_more_research: bool = field(default=False)
    "Whether additional research is needed"
