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

REFLECTION_PROMPT = """You are a research quality evaluator tasked with assessing the completeness of information gathered about a person's work experience.

Here is the person you are researching: {person}

The following schema shows the key information we need to extract:

<schema>
{info}
</schema>

Here are the research notes collected so far:

<research_notes>
{completed_notes}
</research_notes>

Your task is to evaluate the research completeness and decide whether additional research is needed. Please analyze the notes and provide:

1. **Information Assessment**: For each schema field, evaluate what information has been found:
   - Years of experience: What evidence of career duration exists?
   - Current company: Is the current employer clearly identified?
   - Current role: Is the current job title/position specified?
   - Prior companies: What previous employers have been identified?

2. **Gap Analysis**: Identify what critical information is missing or unclear:
   - Which schema fields have no information?
   - Which fields have partial or ambiguous information?
   - Are there inconsistencies in the data that need clarification?

3. **Research Decision**: Based on your analysis, determine if additional research is needed:
   - If information is satisfactory: Explain why the current data is sufficient
   - If more research is needed: Specify what additional information should be searched for

4. **Reasoning**: Provide clear reasoning for your decision:
   - What makes the current information sufficient or insufficient?
   - What specific gaps would additional research address?
   - How would more research improve the overall profile completeness?

Focus on work experience and career progression as the primary evaluation criteria. Be thorough but concise in your assessment."""

