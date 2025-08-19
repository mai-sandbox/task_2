"""State module defining the state schemas for the people research agent."""

import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, List, Optional

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
class OutputState:
    """Output state containing structured information extracted from research."""
    
    years_experience: Optional[int] = None
    """Total years of professional experience."""
    
    current_company: Optional[str] = None
    """Current company where the person works."""
    
    current_role: Optional[str] = None
    """Current job title or role."""
    
    prior_companies: List[str] = field(default_factory=list)
    """List of previous companies the person has worked at."""
    
    reflection_decision: str = "continue"
    """Decision on whether to continue research ('continue') or finish ('finish')."""
    
    reflection_reasoning: str = ""
    """Reasoning behind the reflection decision."""
    
    extracted_info: dict[str, Any] = field(default_factory=dict)
    """Additional extracted information from the research."""


@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OverallState:
    """Overall state that contains all information throughout the research process."""

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
        "years_of_experience": "Total years of professional experience",
        "current_company": "Current company where the person works",
        "current_role": "Current job title or position",
        "prior_companies": "List of previous companies the person has worked at",
        "education": "Educational background and qualifications",
        "skills": "Key skills and expertise areas",
        "notable_achievements": "Notable achievements or accomplishments"
    })
    "Schema defining what information to extract during research"



