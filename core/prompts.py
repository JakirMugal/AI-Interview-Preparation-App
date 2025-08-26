TOPIC_TREE_PROMPT = (
"""
You are an expert interview coach. Given the following resume/profile text,
produce a comprehensive, well-structured topic tree that captures all
possible interview-relevant areas. Return JSON with this exact schema:


{
"topics": [
{
"topic": "<Area, e.g., Machine Learning>",
"subtopics": ["<Sub1>", "<Sub2>", ...]
},
...
]
}


Rules:
- Include both general and resume-specific topics.
- Keep subtopic names short and file-system safe (avoid slashes/quotes).
- If the resume is sparse, infer reasonable topics.
- Limit to at most 12 topics, each with up to 10 subtopics.
"""
)


QNA_PROMPT_TEMPLATE = (
"""
You are creating interview questions and concise reference answers for the unit: {unit_name}.
Use the provided resume/profile context to stay personalized.

Requirements:
- Generate {n_long} LONG-answer questions with answers ~5–6 lines each.
- Generate {n_short} SHORT-answer questions with answers ~1–3 lines each.
- Mix conceptual, practical, scenario-based, and resume-grounded items.
- Be specific; avoid fluff.

Return JSON with this schema:
{{
    "unit": "{unit_name}",
    "long": [
        {{"q": "...", "a": "..."}},
        ...
    ],
    "short": [
        {{"q": "...", "a": "..."}},
        ...
    ]
}}
"""
)
