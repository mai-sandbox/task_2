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

class StructuredPersonInfo(BaseModel):
    """Structured information about a person after reflection."""
    name: Optional[str] = None
    current_company: Optional[str] = None
    current_role: Optional[str] = None
    years_of_experience: Optional[int] = None
    prior_companies: Optional[list[str]] = None
    linkedin: Optional[str] = None
    email: Optional[str] = None
    additional_notes: Optional[str] = None

class ReflectionResult(BaseModel):
    """Result of the reflection step."""
    structured_info: StructuredPersonInfo
    is_satisfactory: bool
    missing_information: list[str]
    should_redo: bool
    reasoning: str

@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OutputState:
    """Output state defines what is returned to the user."""
    
    structured_info: StructuredPersonInfo
    "Structured information about the person"
    
    reflection: ReflectionResult
    "Result of the reflection analysis"


@dataclass(kw_only=True)
class OverallState:
    """Overall state that includes all intermediate processing steps."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "name": "Full name of the person",
        "current_company": "Current company where the person works", 
        "current_role": "Current job title/role",
        "years_of_experience": "Total years of professional experience",
        "prior_companies": "List of previous companies they worked at",
        "linkedin": "LinkedIn profile URL",
        "email": "Email address"
    })
    "Schema defining what information to extract"

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    reflection_result: ReflectionResult = field(default=None)
    "Result of the reflection step"
    
    structured_info: StructuredPersonInfo = field(default=None)
    "Final structured information about the person"
