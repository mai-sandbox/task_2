QUERY_WRITER_PROMPT = """You are a search query generator tasked with creating targeted search queries to gather specific information about a person.

Here is the person you are researching: {person}

Generate at most {max_search_queries} search queries that will help gather the following information:

<schema>
{info}
</schema>

<user_notes>
{user_notes}
</user_notes>

Your query should:
1. Make sure to look up the right name
2. Use context clues as to the company the person works at (if it isn't concretely provided)
3. Do not hallucinate search terms that will make you miss the persons profile entirely
4. Take advantage of the Linkedin URL if it exists, you can include the raw URL in your search query as that will lead you to the correct page guaranteed.

Create a focused query that will maximize the chances of finding schema-relevant information about the person.
Remember we are interested in determining their work experience mainly."""

INFO_PROMPT = """You are doing web research on people, {people}. 

The following schema shows the type of information we're interested in:

<schema>
{info}
</schema>

You have just scraped website content. Your task is to take clear, organized notes about a person, focusing on topics relevant to our interests.

<Website contents>
{content}
</Website contents>

Here are any additional notes from the user:
<user_notes>
{user_notes}
</user_notes>

Please provide detailed research notes that:
1. Are well-organized and easy to read
2. Focus on topics mentioned in the schema
3. Include specific facts, dates, and figures when available
4. Maintain accuracy of the original content
5. Note when important information appears to be missing or unclear

Remember: Don't try to format the output to match the schema - just take clear notes that capture all relevant information."""

REFLECTION_PROMPT = """You are a research analyst tasked with evaluating and structuring research notes about a person.

Here is the person you researched: {person}

You have completed research and gathered the following notes:
<research_notes>
{completed_notes}
</research_notes>

Your task is to:

1. **EXTRACT STRUCTURED INFORMATION**: Convert the research notes into a structured format based on this schema:
<schema>
{extraction_schema}
</schema>

2. **EVALUATE COMPLETENESS**: Assess whether the research is satisfactory by determining:
   - What information was successfully found
   - What key information is missing or unclear
   - Whether the current information is sufficient for the research goals

3. **MAKE CONTINUATION DECISION**: Decide whether additional research is needed and provide reasoning.

Please respond with a JSON object containing exactly these fields:

```json
{{
  "structured_research_results": {{
    "years_of_experience": "extracted value or 'Not found'",
    "current_company": "extracted value or 'Not found'", 
    "current_role": "extracted value or 'Not found'",
    "prior_companies": "extracted value or 'Not found'"
  }},
  "research_satisfaction_assessment": {{
    "satisfaction_level": "high/medium/low",
    "information_found": ["list of successfully found information"],
    "missing_information": ["list of missing or unclear information"],
    "additional_search_needed": true/false,
    "reasoning": "detailed explanation of why additional research is or isn't needed",
    "suggested_search_queries": ["list of suggested queries if additional research is needed, empty array if not"]
  }}
}}
```

Focus on accuracy and be honest about what information is missing. Only mark satisfaction as "high" if you have comprehensive information for all key fields."""

