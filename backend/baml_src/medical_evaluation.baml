// Medical evaluation types for quality assessment
class CategoryScore {
  score float
  reasoning string
  precision float?
  recall float?
  f1_score float?
}

class CategoryScores {
  follow_up_tasks CategoryScore
  medication_instructions CategoryScore
  client_reminders CategoryScore
  clinician_todos CategoryScore
}

class EvaluationResult {
  overall_score float
  category_scores CategoryScores
  precision float
  recall float
  f1_score float
  overall_reasoning string
  confidence_level "high" | "medium" | "low"
}

// Function to evaluate medical extraction quality
function EvaluateMedicalExtraction(
  predicted_extraction: MedicalExtraction,
  gold_standard: MedicalExtraction,
  evaluation_context: string?
) -> EvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are a medical information extraction quality evaluator. Your task is to assess how well a predicted medical extraction matches the gold standard (correct) extraction.

**Evaluation Criteria:**

1. **Completeness**: Are all important items from the gold standard captured?
2. **Accuracy**: Are the extracted items factually correct?
3. **Relevance**: Are the items relevant to the medical context?
4. **Clarity**: Are descriptions clear and actionable?
5. **Semantic Understanding**: Do items convey the same meaning even if phrased differently?

**Scoring Guidelines:**
- 1.0 = Perfect match (all items correctly extracted with same meaning)
- 0.9 = Excellent (minor differences in phrasing, same meaning)
- 0.8 = Very good (some items missed or added, but core information correct)
- 0.7 = Good (several items missed or added, but major points captured)
- 0.6 = Fair (significant omissions or additions, but main concepts present)
- 0.5 = Poor (major errors or missing critical information)
- 0.0-0.4 = Very poor (major errors, missing key information)

**Category-Specific Evaluation:**

**Follow-up Tasks:**
- Evaluate completeness of scheduled tasks, monitoring requirements, and follow-up appointments
- Consider priority levels and due dates
- Assess if tasks are assigned to correct parties (client vs clinician)

**Medication Instructions:**
- Check medication names, dosages, frequencies, and durations
- Evaluate special instructions and contraindications
- Consider drug interactions and patient-specific instructions

**Client Reminders:**
- Assess patient communication items (appointments, tests, lifestyle changes)
- Evaluate reminder types and priorities
- Check due dates and urgency levels

**Clinician To-Dos:**
- Evaluate staff tasks (referrals, test orders, documentation)
- Assess task types and priorities
- Check assignments and due dates

**Semantic Matching Examples:**
✅ "Schedule blood work" ≈ "Order lab tests"
✅ "Monitor blood sugar daily" ≈ "Check glucose levels every day"
✅ "Take medication twice daily" ≈ "Administer drug 2x per day"
❌ "Schedule blood work" ≠ "Patient has diabetes" (different meaning)

**Evaluation Process:**
1. Compare each category systematically
2. Identify matches, omissions, and additions
3. Assess semantic similarity for matched items
4. Calculate precision, recall, and F1 scores
5. Provide detailed reasoning for each category
6. Determine overall confidence level

**Output Format:**
Provide detailed evaluation with specific examples of matches, omissions, and additions. Explain your reasoning for each category score.

---

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**GOLD STANDARD:**
{{ gold_standard }}

{% if evaluation_context %}
**EVALUATION CONTEXT:**
{{ evaluation_context }}
{% endif %}

Please evaluate the predicted extraction against the gold standard and provide:
1. Overall quality score (0.0-1.0)
2. Category-specific scores with detailed reasoning
3. Precision, recall, and F1 scores
4. Overall reasoning explaining the evaluation
5. Confidence level in your assessment

{{ ctx.output_format }}
"#
}

// Test the evaluation function
test sample_evaluation {
  functions [EvaluateMedicalExtraction]
  args {
    predicted_extraction {
      follow_up_tasks [
        {
          description "Schedule blood work for tomorrow"
          priority "high"
          due_date "tomorrow"
          assigned_to "clinician"
        }
      ]
      medication_instructions [
        {
          medication_name "metformin"
          dosage "500mg"
          frequency "twice daily"
          duration "ongoing"
          special_instructions "for diabetes"
        }
      ]
      client_reminders [
        {
          reminder_type "test"
          description "Blood work appointment tomorrow"
          due_date "tomorrow"
          priority "high"
        }
      ]
      clinician_todos [
        {
          task_type "test_order"
          description "Order blood work including HbA1c"
          priority "high"
          due_date "tomorrow"
        }
      ]
    }
    gold_standard {
      follow_up_tasks [
        {
          description "Schedule blood work for tomorrow"
          priority "high"
          due_date "tomorrow"
          assigned_to "clinician"
        }
      ]
      medication_instructions [
        {
          medication_name "metformin"
          dosage "500mg"
          frequency "twice daily"
          duration "ongoing"
          special_instructions "for diabetes"
        }
      ]
      client_reminders [
        {
          reminder_type "test"
          description "Blood work appointment tomorrow"
          due_date "tomorrow"
          priority "high"
        }
      ]
      clinician_todos [
        {
          task_type "test_order"
          description "Order blood work including HbA1c"
          priority "high"
          due_date "tomorrow"
        }
      ]
    }
  }
}

class TestCase {
  case_id string
  predicted_extraction MedicalExtraction
  gold_standard MedicalExtraction
  transcript string?
}

class AverageCategoryScores {
  follow_up_tasks float
  medication_instructions float
  client_reminders float
  clinician_todos float
}

class EvaluationSummary {
  total_cases int
  average_overall_score float
  average_category_scores AverageCategoryScores
  average_precision float
  average_recall float
  average_f1_score float
}

class MultipleEvaluationResult {
  summary EvaluationSummary
  detailed_results EvaluationResult[]
}

// Function to evaluate multiple test cases and generate comprehensive report
function EvaluateMultipleExtractions(
  test_cases: TestCase[]
) -> MultipleEvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are evaluating multiple medical extraction test cases to generate a comprehensive quality report.

For each test case, evaluate the predicted extraction against the gold standard using the same criteria as the single evaluation function.

**Evaluation Process:**
1. Evaluate each test case individually
2. Calculate average scores across all categories
3. Identify patterns in extraction quality
4. Provide insights on strengths and weaknesses
5. Generate recommendations for improvement

**Report Structure:**
- Summary statistics (averages across all cases)
- Detailed results for each test case
- Quality insights and recommendations

---

**TEST CASES:**
{{ test_cases }}

Please evaluate all test cases and provide:
1. Summary statistics with averages
2. Detailed evaluation results for each case
3. Overall insights about extraction quality patterns
4. Recommendations for improving extraction accuracy

{{ ctx.output_format }}
"#
}

class ConfidenceAnalysis {
  high_confidence_items string[]
  low_confidence_items string[]
  confidence_reasoning string
}

class ConfidenceEvaluationResult {
  evaluation EvaluationResult
  confidence_analysis ConfidenceAnalysis
}

// Function to evaluate extraction with confidence scoring
function EvaluateWithConfidence(
  predicted_extraction: MedicalExtraction,
  gold_standard: MedicalExtraction,
  confidence_threshold: float?
) -> ConfidenceEvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are evaluating medical extraction quality with additional confidence analysis.

**Confidence Assessment:**
- High Confidence: Clear semantic matches, complete information, accurate details
- Medium Confidence: Some ambiguity, minor differences, partial matches
- Low Confidence: Significant differences, missing information, unclear matches

**Confidence Factors:**
1. Semantic clarity of matches
2. Completeness of extraction
3. Accuracy of medical details
4. Consistency with medical domain knowledge
5. Ambiguity in source text

---

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**GOLD STANDARD:**
{{ gold_standard }}

{% if confidence_threshold %}
**CONFIDENCE THRESHOLD:**
{{ confidence_threshold }}
{% endif %}

Please provide:
1. Standard evaluation with scores and reasoning
2. Confidence analysis identifying high/low confidence items
3. Explanation of confidence factors
4. Recommendations for improving confidence

{{ ctx.output_format }}
"#
} 

// Types for adaptive evaluation system
class GoldStandardCase {
  case_id string
  gold_standard MedicalExtraction
  transcript string
  similarity_score float?
}

class EvaluationStrategy {
  strategy_type "single" | "few" | "multiple" | "comprehensive"
  num_standards int
  confidence_level "high" | "medium" | "low"
  reasoning string
}

class AdaptiveConfidenceAnalysis {
  relevance_score float
  evaluation_consistency "high" | "medium" | "low"
  variance_analysis string
}

class AdaptiveCostAnalysis {
  num_llm_calls int
  total_tokens int?
  efficiency_score float
}

class AdaptiveEvaluationResult {
  primary_evaluation EvaluationResult
  strategy_used EvaluationStrategy
  all_evaluations EvaluationResult[]
  aggregated_score float
  confidence_analysis AdaptiveConfidenceAnalysis
  cost_analysis AdaptiveCostAnalysis
}

// Function for adaptive evaluation based on relevance scores
function EvaluateAdaptively(
  predicted_extraction: MedicalExtraction,
  available_standards: GoldStandardCase[],
  evaluation_context: string?
) -> AdaptiveEvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are performing adaptive evaluation of medical extraction quality based on relevance scores.

**Adaptive Strategy Rules:**
- High Relevance (≥0.8): Use single standard evaluation
- Medium Relevance (0.6-0.8): Use 2-3 standards evaluation  
- Low Relevance (0.4-0.6): Use 4-5 standards evaluation
- Very Low Relevance (<0.4): Use 6+ standards evaluation

**Evaluation Process:**
1. Analyze similarity scores of available gold standards
2. Select evaluation strategy based on best match relevance
3. Perform evaluations against selected standards
4. Aggregate results using appropriate method
5. Provide confidence analysis and cost metrics

**Aggregation Methods:**
- Single: Use primary evaluation directly
- Few: Weighted average (primary standard weighted higher)
- Multiple: Average with outlier detection
- Comprehensive: Robust average with variance analysis

**Confidence Assessment:**
- High: Clear semantic match, consistent evaluations
- Medium: Good match with some variance
- Low: Poor match, high variance, uncertain evaluation

---

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**AVAILABLE GOLD STANDARDS:**
{{ available_standards }}

{% if evaluation_context %}
**EVALUATION CONTEXT:**
{{ evaluation_context }}
{% endif %}

Please:
1. Analyze similarity scores and select appropriate strategy
2. Perform evaluations against selected standards
3. Aggregate results based on strategy type
4. Provide confidence analysis and cost metrics
5. Explain reasoning for strategy selection

{{ ctx.output_format }}
"#
}

// Function for embedding-based standard selection
class SelectionStrategy {
  primary_standard GoldStandardCase
  relevance_score float
  strategy_type "single" | "few" | "multiple" | "comprehensive"
  num_standards int
  reasoning string
}

class SimilarityAnalysis {
  top_matches GoldStandardCase[]
  relevance_distribution string
  confidence_level "high" | "medium" | "low"
}

class StandardSelectionResult {
  selected_standards GoldStandardCase[]
  selection_strategy SelectionStrategy
  similarity_analysis SimilarityAnalysis
}

function SelectRelevantStandards(
  predicted_extraction: MedicalExtraction,
  all_standards: GoldStandardCase[],
  max_standards: int?
) -> StandardSelectionResult {
  client "openai/gpt-4o"
  prompt #"
You are selecting the most relevant gold standards for evaluation based on semantic similarity.

**Selection Criteria:**
- Semantic similarity to predicted extraction
- Medical context relevance
- Completeness of gold standard
- Diversity of selected standards

**Strategy Selection:**
- Single (1): Best match ≥0.8 similarity
- Few (2-3): Best match 0.6-0.8 similarity
- Multiple (4-5): Best match 0.4-0.6 similarity
- Comprehensive (6+): Best match <0.4 similarity

**Selection Process:**
1. Calculate semantic similarity for all standards
2. Rank standards by similarity score
3. Select appropriate number based on best match
4. Ensure diversity in selected standards
5. Provide reasoning for selection

---

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**ALL AVAILABLE STANDARDS:**
{{ all_standards }}

{% if max_standards %}
**MAX STANDARDS TO SELECT:**
{{ max_standards }}
{% endif %}

Please:
1. Analyze semantic similarity to all standards
2. Select most relevant standards based on strategy
3. Ensure diversity in selected standards
4. Provide detailed reasoning for selection
5. Include similarity analysis and confidence assessment

{{ ctx.output_format }}
"#
}

// Function for comprehensive multi-standard evaluation
class AggregatedResult {
  overall_score float
  category_scores CategoryScores
  precision float
  recall float
  f1_score float
  confidence_level "high" | "medium" | "low"
}

class EvaluationInsights {
  best_matching_standard int
  worst_matching_standard int
  score_variance float
  consistency_level "high" | "medium" | "low"
  outlier_detection string[]
}

class CostMetrics {
  num_evaluations int
  estimated_tokens int
  efficiency_score float
}

class MultiStandardResult {
  individual_evaluations EvaluationResult[]
  aggregated_result AggregatedResult
  evaluation_insights EvaluationInsights
  cost_metrics CostMetrics
}

function EvaluateWithMultipleStandards(
  predicted_extraction: MedicalExtraction,
  selected_standards: GoldStandardCase[],
  aggregation_method: "weighted" | "average" | "robust"
) -> MultiStandardResult {
  client "openai/gpt-4o"
  prompt #"
You are evaluating medical extraction quality against multiple gold standards and aggregating results.

**Aggregation Methods:**
- weighted: Weight by similarity score (higher similarity = higher weight)
- average: Simple arithmetic mean of all evaluations
- robust: Mean with outlier detection and removal

**Evaluation Process:**
1. Evaluate extraction against each selected standard
2. Calculate individual scores and reasoning
3. Aggregate results using specified method
4. Detect and handle outliers
5. Assess consistency across evaluations

**Consistency Assessment:**
- High: All scores within 0.2 range
- Medium: Scores within 0.4 range
- Low: Scores vary by more than 0.4

**Outlier Detection:**
- Identify evaluations that differ significantly from others
- Consider medical context when assessing outliers
- Provide reasoning for outlier identification

---

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**SELECTED STANDARDS:**
{{ selected_standards }}

**AGGREGATION METHOD:**
{{ aggregation_method }}

Please:
1. Evaluate against each selected standard
2. Aggregate results using specified method
3. Assess consistency and detect outliers
4. Provide detailed insights and cost metrics
5. Explain aggregation reasoning and confidence

{{ ctx.output_format }}
"#
}

// Function for cost-effective single standard evaluation
class EfficiencyMetrics {
  num_llm_calls int
  estimated_tokens int
  relevance_score float
  confidence_level "high" | "medium" | "low"
}

class QualityAssessment {
  standard_relevance string
  evaluation_reliability string
  potential_biases string[]
}

class SingleStandardResult {
  evaluation EvaluationResult
  efficiency_metrics EfficiencyMetrics
  quality_assessment QualityAssessment
}

function EvaluateWithSingleStandard(
  predicted_extraction: MedicalExtraction,
  primary_standard: GoldStandardCase,
  evaluation_context: string?
) -> SingleStandardResult {
  client "openai/gpt-4o"
  prompt #"
You are performing a cost-effective single standard evaluation for high-relevance cases.

**Single Standard Evaluation:**
- Use when best match has ≥0.8 similarity
- Focus on detailed, thorough evaluation
- Consider potential biases of single standard
- Provide confidence in evaluation reliability

**Evaluation Quality:**
- Assess completeness of gold standard
- Consider potential biases or limitations
- Evaluate semantic match quality
- Provide confidence assessment

**Efficiency Focus:**
- Single LLM call for evaluation
- Detailed reasoning for confidence
- Cost-benefit analysis
- Quality assurance measures

---

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**PRIMARY STANDARD:**
{{ primary_standard }}

{% if evaluation_context %}
**EVALUATION CONTEXT:**
{{ evaluation_context }}
{% endif %}

Please:
1. Perform thorough evaluation against primary standard
2. Assess standard relevance and potential biases
3. Provide detailed confidence assessment
4. Include efficiency metrics and quality analysis
5. Explain reasoning for single standard approach

{{ ctx.output_format }}
"#
} 