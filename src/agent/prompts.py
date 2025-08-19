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

REFLECTION_PROMPT = """You are an expert research evaluator tasked with assessing the completeness and quality of research about a person's professional background.

Person being researched:
{person}

Structured information extracted from research:
{structured_info}

Raw research notes:
{raw_notes}

User's specific requirements:
{user_notes}

Your task is to evaluate the research and determine:

1. **Completeness Assessment**: Evaluate whether the following critical information has been found:
   - Years of professional experience (specific number or reasonable estimate)
   - Current company name (where they currently work)
   - Current role/position (their job title)
   - Prior companies (at least 2-3 previous employers with roles if they have work history)
   - Educational background (degrees, institutions)
   - Key skills or expertise areas

2. **Quality Evaluation**: Consider:
   - Is the information specific and detailed enough?
   - Are there contradictions or uncertainties in the data?
   - Does the information appear current and reliable?
   - Are the most important professional details captured?

3. **Missing Information**: Identify what critical information is still missing:
   - Be specific about what wasn't found
   - Prioritize information that's most important for understanding their professional background
   - Consider if the missing information is likely findable through web search

4. **Decision Reasoning**: Provide clear reasoning for your decision:
   - If SATISFACTORY: Explain why the current information is sufficient
   - If NEEDS MORE RESEARCH: Explain what specific gaps need to be filled
   - Consider the user's specific requirements when making this decision

5. **Suggested Queries**: If research needs to continue, provide 2-3 specific search queries that would help find the missing information. Focus on:
   - Queries that target the specific missing information
   - Alternative search strategies (e.g., searching company + role if name searches aren't working)
   - LinkedIn-specific searches if professional details are missing

Make your evaluation based on professional research standards. The research should provide enough information to understand the person's:
- Career trajectory and experience level
- Current professional position
- Work history and career progression
- Educational and skill background

Be pragmatic - if the core information (experience, current company, role, prior companies) is present and reliable, the research can be considered satisfactory even if some minor details are missing."""

