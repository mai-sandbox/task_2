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

REFLECTION_PROMPT = """You are a research analyst tasked with evaluating the completeness of research notes about a person and extracting structured information.

Here are the research notes you need to analyze:

<research_notes>
{completed_notes}
</research_notes>

Your task is to:

1. **Extract structured information** about the person, focusing on these key areas:
   - Years of experience: Total years of professional work experience
   - Current company: The organization they currently work for
   - Role: Their current job title or position
   - Prior companies: List of previous companies they have worked at

2. **Evaluate research completeness** by analyzing:
   - How much of the key information is clearly documented
   - What important details might be missing or unclear
   - Whether the information is sufficient for a comprehensive profile

3. **Make a decision** about whether additional research is needed based on:
   - Completeness of the four key information areas
   - Quality and reliability of the information found
   - Whether there are significant gaps that would benefit from more research

Please provide your analysis in a structured format that includes:
- The extracted information for each key area
- A satisfaction score (0.0 to 1.0) indicating how complete the research is
- A list of any missing or unclear information
- A clear decision on whether more research is needed
- Your reasoning for the satisfaction score and research decision

Be thorough in your analysis but decisive in your recommendations. If the core information (years of experience, current company, role, and at least some prior companies) is well-documented, you may recommend ending the research. If key information is missing or unclear, recommend continuing research with specific areas to focus on."""
