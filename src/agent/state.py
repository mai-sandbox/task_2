from dataclasses import dataclass, field
from typing import Any, Optional, Annotated
import operator

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
        "years_of_experience": "Total years of professional work experience",
        "current_company": "Name of the current company or organization",
        "current_role": "Current job title or position",
        "prior_companies": "List of previous companies or organizations worked at",
        "education": "Educational background and qualifications",
        "skills": "Key professional skills and competencies",
        "achievements": "Notable accomplishments or awards"
    })
    "Schema defining the information we want to extract about the person"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines the final structured research results."""
    
    person: Person
    "The person that was researched."
    
    years_of_experience: Optional[str] = field(default=None)
    "Total years of professional work experience extracted from research."
    
    current_company: Optional[str] = field(default=None)
    "Current company or organization the person works at."
    
    current_role: Optional[str] = field(default=None)
    "Current job title or position."
    
    prior_companies: list[str] = field(default_factory=list)
    "List of previous companies or organizations worked at."
    
    education: Optional[str] = field(default=None)
    "Educational background and qualifications."
    
    skills: list[str] = field(default_factory=list)
    "Key professional skills and competencies."
    
    achievements: list[str] = field(default_factory=list)
    "Notable accomplishments or awards."
    
    research_satisfaction: str = field(default="incomplete")
    "Assessment of research completeness: 'satisfied', 'needs_more_research', or 'incomplete'."
    
    missing_information: list[str] = field(default_factory=list)
    "List of information categories that are still missing or incomplete."
    
    reasoning: Optional[str] = field(default=None)
    "Detailed reasoning for the satisfaction assessment and any decisions made."
    
    completed_notes: list[str] = field(default_factory=list)
    "All research notes collected during the process."



