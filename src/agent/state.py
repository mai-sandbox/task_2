from dataclasses import dataclass, field
from typing import Any, Optional, Annotated, List, Dict
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
    """Overall state for the research agent workflow."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    extraction_schema: Dict[str, Any] = field(default_factory=lambda: {
        "years_of_experience": "Total years of professional experience",
        "current_company": "Name of the current employer/company",
        "current_role": "Current job title or position",
        "prior_companies": "List of previous companies worked at with roles and duration if available",
        "education": "Educational background including degrees and institutions",
        "skills": "Key technical and professional skills",
        "notable_achievements": "Significant accomplishments or projects"
    })
    "Schema defining the structured information to extract about the person"
    
    structured_output: Optional[Dict[str, Any]] = field(default=None)
    "Structured information extracted from the research"
    
    reflection_result: Optional[Dict[str, Any]] = field(default=None)
    "Result of the reflection step including satisfaction assessment and reasoning"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines the final structured output from the research agent."""
    
    person: Person
    "The person that was researched"
    
    structured_output: Dict[str, Any] = field(default_factory=dict)
    "Final structured information about the person including years of experience, companies, roles, etc."
    
    research_quality: Optional[Dict[str, Any]] = field(default=None)
    "Assessment of research quality and completeness"
    
    raw_notes: Optional[List[str]] = field(default=None)
    "Raw research notes collected during the process"



