"""
Smart context selector for optimized memory context building
"""
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class ContextCandidate:
    transcript_id: int
    text: str
    similarity_score: float
    user_id: int
    extraction_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ScoredContext:
    candidate: ContextCandidate
    relevance_score: float
    medical_relevance: float
    extraction_quality: float
    context_completeness: float
    estimated_tokens: int
    reasoning: str

class SmartContextSelector:
    def __init__(self, max_tokens: int = 2000, min_relevance_threshold: float = 0.6):
        self.max_tokens = max_tokens
        self.min_relevance_threshold = min_relevance_threshold
        
        # Medical keywords for relevance scoring
        self.medical_keywords = {
            'medication': ['prescribe', 'medication', 'drug', 'dosage', 'frequency', 'duration'],
            'follow_up': ['schedule', 'follow-up', 'appointment', 'return', 'monitor'],
            'tests': ['blood work', 'lab test', 'x-ray', 'mri', 'ct scan', 'ultrasound'],
            'symptoms': ['pain', 'symptom', 'condition', 'diagnosis', 'treatment'],
            'vitals': ['blood pressure', 'heart rate', 'temperature', 'weight', 'height']
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
    
    def assess_medical_relevance(self, query_text: str, context_text: str) -> float:
        """Assess medical relevance between query and context"""
        query_lower = query_text.lower()
        context_lower = context_text.lower()
        
        relevance_score = 0.0
        total_keywords = 0
        
        for category, keywords in self.medical_keywords.items():
            category_score = 0
            category_keywords = 0
            
            for keyword in keywords:
                if keyword in query_lower and keyword in context_lower:
                    category_score += 1
                category_keywords += 1
            
            if category_keywords > 0:
                relevance_score += (category_score / category_keywords) * 0.2  # Each category worth 0.2
        
        # Additional relevance based on medical terms overlap
        medical_terms_query = set(re.findall(r'\b(medication|prescribe|dosage|schedule|test|appointment|monitor|symptom|diagnosis)\b', query_lower))
        medical_terms_context = set(re.findall(r'\b(medication|prescribe|dosage|schedule|test|appointment|monitor|symptom|diagnosis)\b', context_lower))
        
        if medical_terms_query and medical_terms_context:
            overlap = len(medical_terms_query.intersection(medical_terms_context))
            union = len(medical_terms_query.union(medical_terms_context))
            relevance_score += (overlap / union) * 0.3
        
        return min(relevance_score, 1.0)
    
    def assess_extraction_quality(self, extraction_data: Optional[Dict[str, Any]]) -> float:
        """Assess the quality of extraction data"""
        if not extraction_data:
            return 0.0
        
        quality_score = 0.0
        total_items = 0
        
        # Check each category for quality indicators
        categories = ['follow_up_tasks', 'medication_instructions', 'client_reminders', 'clinician_todos']
        
        for category in categories:
            items = extraction_data.get(category, [])
            if items:
                # Quality indicators: completeness, specificity, actionability
                category_score = 0
                for item in items:
                    if isinstance(item, dict):
                        # Check for specific, actionable content
                        description = item.get('description', '')
                        if len(description) > 10:  # Not too short
                            if any(word in description.lower() for word in ['schedule', 'order', 'prescribe', 'monitor', 'test']):
                                category_score += 1
                        if item.get('priority'):  # Has priority
                            category_score += 0.5
                        if item.get('due_date'):  # Has due date
                            category_score += 0.5
                
                if items:
                    quality_score += (category_score / len(items)) * 0.25  # Each category worth 0.25
                total_items += len(items)
        
        return min(quality_score, 1.0)
    
    def assess_context_completeness(self, text: str) -> float:
        """Assess how complete and informative the context is"""
        if not text:
            return 0.0
        
        completeness_score = 0.0
        
        # Length factor (not too short, not too long)
        text_length = len(text)
        if 100 <= text_length <= 2000:
            completeness_score += 0.3
        elif text_length > 2000:
            completeness_score += 0.2
        
        # Medical content factor
        medical_terms = re.findall(r'\b(medication|prescribe|dosage|schedule|test|appointment|monitor|symptom|diagnosis|treatment)\b', text.lower())
        if medical_terms:
            completeness_score += min(len(medical_terms) * 0.1, 0.4)
        
        # Structure factor (has some structure)
        if any(char in text for char in [':', '-', '•', '*']):
            completeness_score += 0.2
        
        # Action factor (contains actionable items)
        action_words = ['schedule', 'order', 'prescribe', 'monitor', 'test', 'refer']
        if any(word in text.lower() for word in action_words):
            completeness_score += 0.1
        
        return min(completeness_score, 1.0)
    
    def calculate_combined_relevance(self, candidate: ContextCandidate, query_text: str) -> ScoredContext:
        """Calculate combined relevance score for a context candidate"""
        # Base similarity score
        similarity_score = candidate.similarity_score
        
        # Medical relevance
        medical_relevance = self.assess_medical_relevance(query_text, candidate.text)
        
        # Extraction quality
        extraction_quality = self.assess_extraction_quality(candidate.extraction_data)
        
        # Context completeness
        context_completeness = self.assess_context_completeness(candidate.text)
        
        # Combined relevance score (weighted)
        relevance_score = (
            similarity_score * 0.4 +
            medical_relevance * 0.3 +
            extraction_quality * 0.2 +
            context_completeness * 0.1
        )
        
        # Estimate tokens
        estimated_tokens = self.estimate_tokens(candidate.text)
        
        # Generate reasoning
        reasoning = f"Similarity: {similarity_score:.3f}, Medical: {medical_relevance:.3f}, Quality: {extraction_quality:.3f}, Completeness: {context_completeness:.3f}"
        
        return ScoredContext(
            candidate=candidate,
            relevance_score=relevance_score,
            medical_relevance=medical_relevance,
            extraction_quality=extraction_quality,
            context_completeness=context_completeness,
            estimated_tokens=estimated_tokens,
            reasoning=reasoning
        )
    
    def select_optimal_context(self, query_text: str, candidates: List[ContextCandidate]) -> List[ContextCandidate]:
        """Select optimal context based on multi-factor scoring"""
        if not candidates:
            return []
        
        # Score all candidates
        scored_candidates = []
        for candidate in candidates:
            scored = self.calculate_combined_relevance(candidate, query_text)
            scored_candidates.append(scored)
        
        # Sort by relevance score
        scored_candidates.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Select optimal context with token limits
        selected_candidates = []
        total_tokens = 0
        
        for scored in scored_candidates:
            # Check relevance threshold
            if scored.relevance_score < self.min_relevance_threshold:
                break
            
            # Check token limits
            if total_tokens + scored.estimated_tokens > self.max_tokens:
                break
            
            # Check for diminishing returns (if we have enough high-quality context)
            if len(selected_candidates) >= 3 and scored.relevance_score < 0.8:
                # If we have 3+ high-quality contexts, be more selective
                if scored.relevance_score < 0.9:
                    break
            
            selected_candidates.append(scored.candidate)
            total_tokens += scored.estimated_tokens
            
            # Early termination if we have sufficient context
            if len(selected_candidates) >= 5:
                break
        
        return selected_candidates
    
    def build_memory_context(self, query_text: str, selected_candidates: List[ContextCandidate]) -> str:
        """Build memory context from selected candidates (transcript only)"""
        if not selected_candidates:
            return ""
        
        memory_parts = []
        
        # Separate test cases and user transcripts
        test_cases = [c for c in selected_candidates if c.user_id == 999]
        user_transcripts = [c for c in selected_candidates if c.user_id != 999]
        
        # Add test cases first (for few-shot learning)
        if test_cases:
            memory_parts.append("RELEVANT EXAMPLE CASES:")
            for i, candidate in enumerate(test_cases[:3]):  # Limit to 3
                memory_parts.append(f"Example Case {i+1}:")
                memory_parts.append(candidate.text[:500] + "..." if len(candidate.text) > 500 else candidate.text)
                memory_parts.append("")
        
        # Add previous visits
        if user_transcripts:
            memory_parts.append("PREVIOUS VISITS:")
            for i, candidate in enumerate(user_transcripts[:3]):  # Limit to 3
                memory_parts.append(f"Previous Visit {i+1} (Transcript ID: {candidate.transcript_id}):")
                memory_parts.append(candidate.text[:500] + "..." if len(candidate.text) > 500 else candidate.text)
                memory_parts.append("")
        
        return "\n".join(memory_parts)
    
    def build_memory_context_with_extractions(self, query_text: str, selected_candidates: List[ContextCandidate]) -> str:
        """Build memory context from selected candidates including their extractions"""
        if not selected_candidates:
            return ""
        
        memory_parts = []
        
        # Separate test cases and user transcripts
        test_cases = [c for c in selected_candidates if c.user_id == 999]
        user_transcripts = [c for c in selected_candidates if c.user_id != 999]
        
        # Add test cases first (for few-shot learning)
        if test_cases:
            memory_parts.append("RELEVANT EXAMPLE CASES:")
            for i, candidate in enumerate(test_cases[:3]):  # Limit to 3
                memory_parts.append(f"Example Case {i+1}:")
                memory_parts.append("TRANSCRIPT:")
                memory_parts.append(candidate.text[:500] + "..." if len(candidate.text) > 500 else candidate.text)
                
                # Add extraction if available
                if candidate.extraction_data:
                    memory_parts.append("EXTRACTIONS:")
                    extraction_data = candidate.extraction_data
                    
                    if extraction_data.get("follow_up_tasks"):
                        memory_parts.append("Follow-up Tasks:")
                        for task in extraction_data["follow_up_tasks"][:2]:  # Limit to 2 tasks
                            memory_parts.append(f"  - {task.get('description', 'N/A')} (Priority: {task.get('priority', 'N/A')})")
                    
                    if extraction_data.get("medication_instructions"):
                        memory_parts.append("Medication Instructions:")
                        for med in extraction_data["medication_instructions"][:2]:  # Limit to 2 medications
                            memory_parts.append(f"  - {med.get('medication_name', 'N/A')} {med.get('dosage', 'N/A')} {med.get('frequency', 'N/A')}")
                    
                    if extraction_data.get("client_reminders"):
                        memory_parts.append("Client Reminders:")
                        for reminder in extraction_data["client_reminders"][:2]:  # Limit to 2 reminders
                            memory_parts.append(f"  - {reminder.get('description', 'N/A')} ({reminder.get('reminder_type', 'N/A')})")
                    
                    if extraction_data.get("clinician_todos"):
                        memory_parts.append("Clinician To-Dos:")
                        for todo in extraction_data["clinician_todos"][:2]:  # Limit to 2 todos
                            memory_parts.append(f"  - {todo.get('description', 'N/A')} ({todo.get('task_type', 'N/A')})")
                
                memory_parts.append("")
        
        # Add previous visits
        if user_transcripts:
            memory_parts.append("PREVIOUS VISITS:")
            for i, candidate in enumerate(user_transcripts[:3]):  # Limit to 3
                memory_parts.append(f"Previous Visit {i+1} (Transcript ID: {candidate.transcript_id}):")
                memory_parts.append("TRANSCRIPT:")
                memory_parts.append(candidate.text[:500] + "..." if len(candidate.text) > 500 else candidate.text)
                
                # Add extraction if available
                if candidate.extraction_data:
                    memory_parts.append("EXTRACTIONS:")
                    extraction_data = candidate.extraction_data
                    
                    if extraction_data.get("follow_up_tasks"):
                        memory_parts.append("Follow-up Tasks:")
                        for task in extraction_data["follow_up_tasks"][:2]:  # Limit to 2 tasks
                            memory_parts.append(f"  - {task.get('description', 'N/A')} (Priority: {task.get('priority', 'N/A')})")
                    
                    if extraction_data.get("medication_instructions"):
                        memory_parts.append("Medication Instructions:")
                        for med in extraction_data["medication_instructions"][:2]:  # Limit to 2 medications
                            memory_parts.append(f"  - {med.get('medication_name', 'N/A')} {med.get('dosage', 'N/A')} {med.get('frequency', 'N/A')}")
                    
                    if extraction_data.get("client_reminders"):
                        memory_parts.append("Client Reminders:")
                        for reminder in extraction_data["client_reminders"][:2]:  # Limit to 2 reminders
                            memory_parts.append(f"  - {reminder.get('description', 'N/A')} ({reminder.get('reminder_type', 'N/A')})")
                    
                    if extraction_data.get("clinician_todos"):
                        memory_parts.append("Clinician To-Dos:")
                        for todo in extraction_data["clinician_todos"][:2]:  # Limit to 2 todos
                            memory_parts.append(f"  - {todo.get('description', 'N/A')} ({todo.get('task_type', 'N/A')})")
                
                memory_parts.append("")
        
        return "\n".join(memory_parts)

# Global instance
smart_context_selector = SmartContextSelector() 