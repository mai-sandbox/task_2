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

REFLECTION_PROMPT = """You are a research analyst tasked with evaluating the completeness and quality of research notes about a person.

PERSON BEING RESEARCHED: {person}

RESEARCH NOTES:
{notes}

TARGET INFORMATION SCHEMA:
{schema}

Your task is to:
1. Extract structured information from the research notes
2. Evaluate the completeness and quality of the information
3. Identify any missing critical information
4. Determine if additional research is needed
5. Suggest specific search queries if more research is required

Focus particularly on these key areas:
- Years of experience (try to calculate from career timeline)
- Current company and role
- Previous companies and roles with approximate dates
- Career progression and timeline

ANALYSIS CRITERIA:
- Confidence Score: Rate from 0.0 to 1.0 based on:
  - How complete is the information (0.8+ means most key fields are filled)
  - How reliable are the sources
  - How recent is the information
  - How specific are the details (exact vs approximate)

- Missing Information: Identify specific gaps like:
  - "Years of experience not calculable from available data"
  - "Current role unclear or outdated"
  - "Employment gaps between [dates]"
  - "No information about [specific company] role"

- Additional Research Needed: Determine if confidence is below 0.7 OR critical information is missing

- Search Query Suggestions: If more research needed, suggest 2-3 specific queries like:
  - "[Person name] [current company] 2024" (for recent info)
  - "[Person name] LinkedIn work experience" (for career details)
  - "[Person name] [previous company] tenure dates" (for specific gaps)

Provide your analysis in the structured format requested, being precise about what information is available vs missing."""
