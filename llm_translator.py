import os
import google.generativeai as genai

class GeminiTranslator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        
        genai.configure(api_key=self.api_key)
        
        # Primary model: Gemini 3 Flash
        self.model_primary = genai.GenerativeModel('gemini-3-flash-preview')
        self.primary_model_name = "gemini-3-flash"
        
        # Fallback model: Gemini 2.5 Pro
        self.model_fallback = genai.GenerativeModel('gemini-2.5-pro')
        self.fallback_model_name = "gemini-2.5-pro"
        
        # Track which model was used
        self.last_used_model = self.primary_model_name
        
    def _generate_with_retry(self, prompt, retries=3):
        import time
        
        # Try primary model first
        for i in range(retries):
            try:
                response = self.model_primary.generate_content(prompt)
                time.sleep(4)  # Rate limit handling
                self.last_used_model = self.primary_model_name
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                
                # Check if quota exceeded
                if "429" in error_str or "Quota exceeded" in error_str or "quota" in error_str.lower():
                    if i < retries - 1:
                        wait = (i + 1) * 10
                        print(f"    ⚠️  Gemini 3 Flash quota exceeded. Waiting {wait}s...")
                        time.sleep(wait)
                        continue
                    else:
                        # All retries failed, switch to fallback model
                        print(f"    🔄 Switching to {self.fallback_model_name}...")
                        break
                else:
                    print(f"Error generating content: {e}")
                    return ""
        
        # Fallback to Gemini 2.0
        try:
            response = self.model_fallback.generate_content(prompt)
            time.sleep(4)
            self.last_used_model = self.fallback_model_name
            print(f"    ✅ Successfully used {self.fallback_model_name}")
            return response.text.strip()
        except Exception as e:
            print(f"Error with fallback model: {e}")
            return ""
    
    def get_last_used_model(self):
        """Return the name of the last used model"""
        return self.last_used_model
    
    def analyze_paper(self, title, abstract, authors):
        """
        Analyze paper and return all summaries in one go (JSON format).
        Returns dict with: short_summary, detailed_summary, architecture
        """
        if not abstract:
            return {
                "short_summary": "요약 없음",
                "detailed_summary": "",
                "architecture": ""
            }
            
        prompt = f"""다음 논문을 분석하여 정보를 추출하고 반드시 **JSON 형식**으로만 출력하세요.

논문 제목: {title}
저자: {', '.join(authors[:3])}
초록: {abstract}

다음 키를 가진 JSON 객체를 생성하세요:
1. "short_summary": 논문의 핵심 내용을 **한 문장**으로 요약 (한국어)
2. "detailed_summary": 논문에 대한상세 요약 (2-3문단, 한국어). 문제 정의, 방법론, 결과를 포함.
3. "architecture": 제안하는 Architecture 또는 방법론에 대한 간략한 설명 (2-3문장, 한국어)

출력 예시:
{{
  "short_summary": "...",
  "detailed_summary": "...",
  "architecture": "..."
}}
"""
        response_text = self._generate_with_retry(prompt)
        
        # Parse JSON
        import json
        import re
        
        try:
            # Remove markdown code blocks if present
            clean_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            data = json.loads(clean_text)
            return {
                "short_summary": data.get("short_summary", "요약 실패"),
                "detailed_summary": data.get("detailed_summary", ""),
                "architecture": data.get("architecture", "")
            }
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response_text}")
            return {
                "short_summary": "요약 파싱 실패",
                "detailed_summary": response_text, # Fallback to raw text
                "architecture": ""
            }

    def analyze_papers_batch(self, papers_data):
        """
        Analyze multiple papers in one API call (batch processing).
        papers_data: list of dicts with 'title', 'abstract', 'authors'
        Returns: tuple of (list of dicts with analysis results, model_name)
        """
        if not papers_data:
            return [], "none"
        
        # Build batch prompt
        papers_text = ""
        for idx, paper in enumerate(papers_data):
            authors_str = ', '.join(paper.get('authors', [])[:3])
            papers_text += f"""
---
논문 {idx + 1}:
제목: {paper['title']}
저자: {authors_str}
초록: {paper.get('abstract', 'No abstract available')}
"""
        
        prompt = f"""다음 {len(papers_data)}개의 논문을 각각 분석하여 JSON 배열로 출력하세요.

{papers_text}

각 논문에 대해 다음 키를 가진 JSON 객체를 생성하세요:
1. "paper_index": 논문 번호 (1부터 시작)
2. "short_summary": 논문의 핵심 내용을 **한 문장**으로 요약 (한국어)
3. "detailed_summary": 논문에 대한 상세 요약 (2-3문단, 한국어). 문제 정의, 방법론, 결과를 포함.
4. "architecture": 제안하는 Architecture 또는 방법론에 대한 간략한 설명 (2-3문장, 한국어)

출력 형식 (JSON 배열):
[
  {{
    "paper_index": 1,
    "short_summary": "...",
    "detailed_summary": "...",
    "architecture": "..."
  }},
  {{
    "paper_index": 2,
    "short_summary": "...",
    "detailed_summary": "...",
    "architecture": "..."
  }}
]
"""
        
        response_text = self._generate_with_retry(prompt)
        used_model = self.last_used_model
        
        # Parse JSON array
        import json
        import re
        
        try:
            # Remove markdown code blocks if present
            clean_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            data = json.loads(clean_text)
            
            # Ensure it's a list
            if not isinstance(data, list):
                raise ValueError("Response is not a JSON array")
            
            # Map results back to papers
            results = []
            for paper_data in papers_data:
                results.append({
                    "short_summary": "요약 없음",
                    "detailed_summary": "",
                    "architecture": ""
                })
            
            # Fill in results from API response
            for item in data:
                idx = item.get("paper_index", 0) - 1
                if 0 <= idx < len(results):
                    results[idx] = {
                        "short_summary": item.get("short_summary", "요약 실패"),
                        "detailed_summary": item.get("detailed_summary", ""),
                        "architecture": item.get("architecture", "")
                    }
            
            return results, used_model
            
        except Exception as e:
            print(f"Error parsing batch JSON: {e}")
            print(f"Raw response: {response_text[:500]}...")
            # Return empty results for all papers
            return [{
                "short_summary": "배치 요약 실패",
                "detailed_summary": "",
                "architecture": ""
            } for _ in papers_data], used_model

    # Legacy methods removed to enforce single call usage

