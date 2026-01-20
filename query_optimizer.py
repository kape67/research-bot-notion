import google.generativeai as genai
import os
import json
from typing import Dict

class QueryOptimizer:
    """Optimize user queries using Gemini AI for better search results"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
    
    def optimize_query(self, user_query: str) -> Dict[str, str]:
        """
        Optimize user query for different search engines
        
        Args:
            user_query: Original user query (can be in any language)
            
        Returns:
            Dictionary with optimized queries for each search engine:
            {
                'semantic_scholar': '...',
                'arxiv': '...',
                'duckduckgo': '...',
                'original': '...'
            }
        """
        
        prompt = f"""You are a research paper search query optimizer. Given a user's search query, generate optimized search queries for three different academic search engines.

User Query: "{user_query}"

Please analyze the query and generate three optimized versions:

1. **Semantic Scholar**: This API accepts natural language queries well. Include key concepts and context. If the query is in Korean or another language, translate to English.

2. **arXiv**: This requires concise, keyword-based queries. Use technical terms and avoid long phrases. Focus on the core research topic.

3. **DuckDuckGo**: This is a web search engine. Create a natural search query that includes "research paper" or "academic paper" context to get better results.

Guidelines:
- If the input is in Korean (or non-English), translate to English
- Extract the core research topic and key concepts
- Keep queries focused and relevant
- For recent/latest requests, include temporal keywords appropriately

Return ONLY a valid JSON object with this exact structure (no markdown, no code blocks, just the JSON):
{{
    "semantic_scholar": "optimized query for Semantic Scholar",
    "arxiv": "optimized query for arXiv",
    "duckduckgo": "optimized query for DuckDuckGo"
}}"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                # Find the actual JSON content
                lines = result_text.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('{'):
                        in_json = True
                    if in_json:
                        json_lines.append(line)
                    if line.strip().endswith('}') and in_json:
                        break
                result_text = '\n'.join(json_lines)
            
            # Parse JSON response
            optimized = json.loads(result_text)
            
            # Add original query
            optimized['original'] = user_query
            
            return optimized
            
        except json.JSONDecodeError as e:
            print(f"  ⚠️  Failed to parse Gemini response as JSON: {e}")
            print(f"  Raw response: {response.text}")
            # Fallback to original query for all engines
            return {
                'semantic_scholar': user_query,
                'arxiv': user_query,
                'duckduckgo': user_query,
                'original': user_query
            }
        except Exception as e:
            print(f"  ⚠️  Query optimization failed: {e}")
            # Fallback to original query for all engines
            return {
                'semantic_scholar': user_query,
                'arxiv': user_query,
                'duckduckgo': user_query,
                'original': user_query
            }
