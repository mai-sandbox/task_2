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

REFLECTION_PROMPT = """You are a research analyst tasked with evaluating and structuring information about a person's professional background.

You have been provided with research notes about: {person}

<research_notes>
{completed_notes}
</research_notes>

Your task is to analyze these notes and extract structured information according to the following schema:

<extraction_schema>
{extraction_schema}
</extraction_schema>

Please perform the following analysis:

1. **EXTRACT STRUCTURED INFORMATION**: Convert the research notes into a structured format that matches the extraction schema. Focus specifically on:
   - Years of experience: Total professional experience and specific durations
   - Current company: Present employer and any relevant details
   - Current role: Job title, responsibilities, and level
   - Prior companies: Previous employers with roles, durations, and key achievements

2. **EVALUATE COMPLETENESS**: Assess how complete the extracted information is on a scale from 0.0 to 1.0:
   - 1.0 = All key information is present and detailed
   - 0.8-0.9 = Most information is present with minor gaps
   - 0.6-0.7 = Some key information is present but significant gaps exist
   - 0.4-0.5 = Limited information with major gaps
   - 0.0-0.3 = Very little or no relevant information found

3. **IDENTIFY MISSING INFORMATION**: List specific categories or details that are missing or incomplete from the research notes.

4. **DECIDE ON CONTINUATION**: Determine whether additional research should be conducted based on:
   - Completeness score (generally continue if < 0.7)
   - Critical missing information
   - Quality and reliability of current information
   - Potential for finding additional relevant data

5. **PROVIDE REASONING**: Explain your assessment, including:
   - What information was successfully extracted
   - Why you assigned the specific completeness score
   - What key information is missing and why it's important
   - Your rationale for recommending to continue or finish research

Guidelines:
- Be thorough but concise in your analysis
- Focus on professional/career information as specified in the schema
- Consider both quantity and quality of information when scoring completeness
- Be realistic about what additional research might uncover
- Prioritize accuracy over completeness - don't fabricate missing information

Your response should be structured to match the OutputState format with clear sections for structured_info, completeness_score, missing_information, should_continue, and reasoning."""

