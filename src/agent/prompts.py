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

REFLECTION_PROMPT = """You are analyzing research notes about a person to extract structured information and assess completeness.

Person being researched:
- Email: {email}
- Name: {name}
- LinkedIn: {linkedin}
- Company: {company}
- Role: {role}

Research notes collected:
{notes}

Your task is to:
1. Extract structured information from the notes, focusing on:
   - Years of experience (calculate from work history if not explicitly stated)
   - Current company and role
   - Prior companies and roles (with durations when available)
   - Educational background
   - Key skills and expertise

2. Assess whether the information is satisfactory by checking:
   - Do we have clear information about their current position?
   - Do we have a reasonable work history (at least 2-3 prior roles)?
   - Can we estimate their years of experience?
   - Do we understand their professional background?

3. Identify what's missing and could be found with more searching:
   - Be specific about what information gaps exist
   - Only list items that are realistically findable through web search

4. Provide reasoning for whether to retry:
   - Consider if missing information is critical
   - Consider if we've already tried {retry_count} times
   - Maximum retries should be 2

Please be thorough in extracting information from the notes, even if some details are incomplete."""
