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


class StructuredPersonInfo(BaseModel):
    """Structured information about a person for research purposes."""
    
    name: Optional[str] = None
    current_company: Optional[str] = None
    current_role: Optional[str] = None
    years_of_experience: Optional[int] = None
    prior_companies: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    education: Optional[str] = None
    linkedin_url: Optional[str] = None


class ReflectionEvaluation(BaseModel):
    """Evaluation of research completeness and quality."""
    
    is_satisfactory: bool
    missing_information: list[str] = field(default_factory=list)
    confidence_score: float  # 0-1 scale
    should_continue_research: bool
    reasoning: str
    suggested_queries: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class OutputState:
    """Output state returned to the user."""
    
    structured_info: Optional[StructuredPersonInfo] = None
    all_notes: str = ""
    reflection: Optional[ReflectionEvaluation] = None


@dataclass(kw_only=True)
class OverallState:
    """Overall state that flows through the graph."""

    person: Person
    "Person to research provided by the user."

    user_notes: Optional[str] = field(default=None)
    "Any notes from the user to start the research process."

    extraction_schema: dict = field(default_factory=lambda: {
        "name": "Full name of the person",
        "current_company": "Current employer/company",
        "current_role": "Current job title/position", 
        "years_of_experience": "Total years of professional experience",
        "prior_companies": "List of previous employers",
        "skills": "Key technical or professional skills",
        "education": "Educational background",
        "linkedin_url": "LinkedIn profile URL"
    })
    "Schema defining what information we want to extract"

    search_queries: list[str] = field(default_factory=list)
    "List of generated search queries to find relevant information"

    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    structured_info: Optional[StructuredPersonInfo] = field(default=None)
    "Structured information extracted from research"
    
    reflection: Optional[ReflectionEvaluation] = field(default=None)
    "Evaluation of research quality and completeness"
