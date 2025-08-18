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

REFLECTION_PROMPT = """You are analyzing research notes about a person to extract structured information and evaluate completeness.

Person being researched: {person}

Research notes collected so far:
<notes>
{notes}
</notes>

Information schema we need to extract:
<schema>
{extraction_schema}
</schema>

User's additional context:
<user_notes>
{user_notes}
</user_notes>

Your task is to:

1. **Extract Structured Information**: Carefully review the notes and extract:
   - Years of experience: Look for total years in their career, time in current role, or career start dates
   - Current company: Their most recent or current employer
   - Role: Their current job title or position
   - Prior companies: List all previous companies mentioned in their work history

2. **Evaluate Completeness**: Assess whether the gathered information is satisfactory:
   - Is the years of experience clearly stated or can it be reasonably inferred?
   - Do we have their current company and role?
   - Do we have a reasonable understanding of their career progression?
   - Are there significant gaps in the work history?

3. **Decide Next Steps**: Based on your evaluation:
   - Choose "stop" if:
     * We have clear information about their current role and company
     * We have at least a general sense of their experience level
     * The core information requested is sufficiently covered
   - Choose "continue" if:
     * Critical information is completely missing (e.g., no current company found)
     * The information is too vague or contradictory
     * We haven't found enough about their professional background

4. **Provide Clear Reasoning**: Explain your decision with specific details:
   - What information was successfully extracted
   - What information is missing or unclear
   - Why you decided to continue or stop the research

Remember: 
- If information is not found in the notes, mark it as "Not found" rather than guessing
- Focus on professional/work experience information
- Be thorough but practical - perfect information isn't always available
- Consider the user's specific needs mentioned in their notes"""

