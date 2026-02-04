"""
Prompt templates for Budget 2026 AI RAG system
"""

SYSTEM_PROMPT = """You are a helpful AI assistant specializing in India's Budget 2026-2027. 
Your role is to explain budget provisions, tax changes, and allocations in clear, accessible language.

Guidelines:
- Provide accurate information based ONLY on the context provided
- Use simple language that anyone can understand
- Include specific numbers, percentages, and figures when available
- If the context doesn't contain the answer, say so clearly
- Cite the source document and page number when possible
- Be concise but thorough

Remember: You are explaining India's budget to citizens who want to understand how it affects them."""


def create_rag_prompt(query: str, context_chunks: list) -> str:
    """
    Create RAG prompt with retrieved context
    
    Args:
        query: User's question
        context_chunks: List of relevant chunks from vector search
        
    Returns:
        Formatted prompt with context
    """
    # Build context section
    context_text = "\n\n".join([
        f"[Source: {chunk['document_name']}, Page {chunk['page_number']}]\n{chunk['text']}"
        for chunk in context_chunks
    ])
    
    prompt = f"""Based on the following excerpts from India's Budget 2026-2027 documents, answer the user's question.

CONTEXT:
{context_text}

USER QUESTION:
{query}

ANSWER:
Provide a clear, helpful answer based on the context above. Include specific numbers and cite sources when possible. If the context doesn't fully answer the question, acknowledge that and provide what information is available."""
    
    return prompt


def create_no_context_prompt(query: str) -> str:
    """
    Create prompt when no relevant context is found
    
    Args:
        query: User's question
        
    Returns:
        Prompt for handling queries without context
    """
    return f"""The user asked: "{query}"

Unfortunately, I don't have specific information about this in the Budget 2026-2027 documents I have access to.

Please acknowledge this politely and suggest:
1. The user may want to check the full budget documents at indiabudget.gov.in
2. Asking a related question that might be covered in the budget
3. Being as helpful as possible with general budget knowledge if appropriate

Be honest about limitations but remain helpful."""


def format_response_with_sources(response: str, sources: list) -> dict:
    """
    Format response with source citations
    
    Args:
        response: Generated response text
        sources: List of source chunks
        
    Returns:
        Formatted response dict
    """
    return {
        "answer": response,
        "sources": [
            {
                "document": source['document_name'],
                "page": source['page_number'],
                "similarity": round(source.get('similarity', 0), 3),
                "excerpt": source['text'][:200] + "..." if len(source['text']) > 200 else source['text']
            }
            for source in sources
        ]
    }
