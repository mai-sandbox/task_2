from dataclasses import dataclass, field
from typing import Any, Optional, Annotated, List
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
class OutputState:
    """Output state represents the final structured research results."""
    
    years_of_experience: Optional[int] = field(default=None)
    "Total years of professional experience"
    
    current_company: Optional[str] = field(default=None)
    "Name of the current employer/company"
    
    current_role: Optional[str] = field(default=None)
    "Current job title or position"
    
    prior_companies: List[str] = field(default_factory=list)
    "List of previous companies the person has worked at"
    
    education: Optional[str] = field(default=None)
    "Educational background and qualifications"
    
    skills: List[str] = field(default_factory=list)
    "Key technical and professional skills"
    
    notable_achievements: List[str] = field(default_factory=list)
    "Significant accomplishments or projects"
    
    research_notes: str = field(default="")
    "Consolidated notes from the research process"
    
    confidence_score: float = field(default=0.0)
    "Confidence score (0-1) indicating completeness of information"
    
    missing_information: List[str] = field(default_factory=list)
    "List of information that could not be found"


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
        "years_of_experience": "Total years of professional experience",
        "current_company": "Name of the current employer/company",
        "current_role": "Current job title or position",
        "prior_companies": "List of previous companies worked at",
        "education": "Educational background and qualifications",
        "skills": "Key technical and professional skills",
        "notable_achievements": "Significant accomplishments or projects"
    })
    "Schema defining the information to extract about the person"
    
    reflection_count: int = field(default=0)
    "Number of reflection iterations performed"
    
    reflection_decision: Optional[str] = field(default=None)
    "Decision from reflection: 'satisfactory' or 'needs_more_research'"
    
    reflection_reasoning: Optional[str] = field(default=None)
    "Reasoning behind the reflection decision"




