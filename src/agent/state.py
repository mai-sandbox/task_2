"""State management module for the people research agent.

This module defines the state classes used throughout the research workflow,
including input/output states and the overall state that tracks research progress.
"""

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

    user_notes: str = field(default="")
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default_factory=list)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_of_experience": {
            "description": "Total years of professional work experience",
            "type": "integer",
            "required": True
        },
        "current_company": {
            "description": "Name of the current employer/company",
            "type": "string",
            "required": True
        },
        "current_role": {
            "description": "Current job title or position",
            "type": "string",
            "required": True
        },
        "prior_companies": {
            "description": "List of previous companies/employers with roles and duration",
            "type": "array",
            "items": {
                "company_name": "string",
                "role": "string",
                "duration": "string",
                "years": "string"
            },
            "required": True
        },
        "education": {
            "description": "Educational background including degrees and institutions",
            "type": "string",
            "required": False
        },
        "skills": {
            "description": "Key professional skills and competencies",
            "type": "array",
            "required": False
        }
    })
    "Schema defining the key information to extract about the person"
    
    # Reflection-related fields
    reflection_output: dict[str, Any] = field(default_factory=dict)
    "Output from the reflection analysis including structured assessment"
    
    research_decision: str = field(default="")
    "Decision from reflection: either 'CONTINUE' or 'CONCLUDE'"
    
    extracted_info: dict[str, Any] = field(default_factory=dict)
    "Structured information extracted from research notes"
    
    missing_information: list[str] = field(default_factory=list)
    "List of information gaps identified during reflection"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines the final structured information returned by the graph."""
    
    person: Person
    "The person that was researched."
    
    extracted_info: dict[str, Any] = field(default_factory=dict)
    "Structured information extracted about the person based on the schema."
    
    research_summary: str = field(default="")
    "Summary of the research process and findings."
    
    confidence_score: float = field(default=0.0)
    "Confidence score (0-1) indicating how complete the extracted information is."
    
    missing_information: list[str] = field(default_factory=list)
    "List of key information areas that could not be found or verified."






