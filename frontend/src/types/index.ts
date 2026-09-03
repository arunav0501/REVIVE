export interface DatasetCounts {
  claims?: number;
  payers?: number;
  payer_policies?: number;
  followups?: number;
  claim_outcomes?: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'error';
  app_name: string;
  version: string;
  phase: number;
  timestamp: string;
  database: {
    status: string;
    database_url: string;
    engine: string;
    error?: string;
  };
  counts?: DatasetCounts;
}

export interface DbHealthCheck {
  status: string;
  scalar_check: number;
  message: string;
  timestamp: string;
  counts?: DatasetCounts;
}

export interface RecommendedAction {
  action_type: string;
  channel: string;
  urgency: string;
  title: string;
  description: string;
  rationale: string;
}

export interface PayerSummary {
  payer_id: string;
  payer_name: string;
  plan_type: string;
  avg_processing_days: number;
  avg_response_days: number;
  filing_deadline_days: number;
  preferred_contact_method: string;
}

export interface FollowupItem {
  followup_id: string;
  claim_id: string;
  followup_date: string;
  channel: string;
  action_type: string;
  message: string;
  payer_response?: string | null;
  response_date?: string | null;
  outcome?: string | null;
}

export interface ClaimOutcome {
  claim_id: string;
  final_outcome: string;
  days_to_resolution: number;
  was_denied: number;
  was_delayed: number;
  recovered_amount: number;
  successful_followup: number;
}

export interface PredictionSummary {
  prediction_id: number;
  claim_id: string;
  denial_probability: number;
  delay_probability: number;
  recovery_probability: number;
  expected_recovery: number;
  priority_score: number;
  priority_band: string;
  model_version: string;
}

export interface ClaimItem {
  claim_id: string;
  patient_id: string;
  provider_id: string;
  payer_id: string;
  payer_name?: string | null;
  claim_date: string;
  service_date: string;
  claim_type: string;
  place_of_service: string;
  billed_amount: number;
  allowed_amount: number;
  paid_amount: number;
  patient_responsibility: number;
  outstanding_amount: number;
  expected_reimbursement: number;
  claim_status: string;
  denial_status?: string | null;
  denial_code?: string | null;
  denial_reason?: string | null;
  days_in_ar: number;
  followup_count: number;
  resubmission_count: number;
  appeal_status: string;
  authorization_required: boolean;
  authorization_status: string;
  network_status: string;
  last_followup_date?: string | null;
  last_payer_response?: string | null;
  days_since_last_response?: number | null;
  delay_probability?: number | null;
  denial_probability?: number | null;
  recovery_probability?: number | null;
  expected_recovery?: number | null;
  priority_score?: number | null;
  priority_band?: string | null;
  explainability_reasons?: string[] | null;
  recommended_action?: RecommendedAction | null;
}

export interface ClaimDetail extends ClaimItem {
  filing_deadline_remaining_days?: number | null;
  payer?: PayerSummary | null;
  followups?: FollowupItem[];
  outcome?: ClaimOutcome | null;
  prediction?: PredictionSummary | null;
}

export interface PaginatedClaims {
  items: ClaimItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ModelMetricDetail {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  test_samples: number;
  train_samples: number;
}

export interface ModelInfo {
  target: string;
  algorithm: string;
  metrics: ModelMetricDetail;
}

export interface MLMetricsResponse {
  model_version: string;
  trained_at: string;
  models: {
    delay_model: ModelInfo;
    denial_model: ModelInfo;
  };
}

export interface PredictionResult {
  claim_id?: string;
  delay_probability: number;
  denial_probability: number;
  recovery_probability: number;
  expected_recovery: number;
  priority_score?: number;
  priority_band?: string;
  explainability_reasons?: string[];
  model_version: string;
}

export interface DashboardMetrics {
  total_ar: number;
  total_claims: number;
  critical_claims: number;
  high_priority_claims: number;
  expected_recovery: number;
  recovered_revenue: number;
  avg_days_in_ar: number;
  denial_rate: number;
}

export interface AgingBucket {
  bucket: string;
  min_days: number;
  max_days?: number | null;
  count: number;
  total_outstanding: number;
  expected_recovery: number;
}

export interface PayerPerformance {
  payer_id: string;
  payer_name: string;
  plan_type: string;
  total_claims: number;
  total_outstanding: number;
  expected_recovery: number;
  avg_processing_days: number;
  avg_response_days: number;
  filing_deadline_days: number;
  denial_rate: number;
}

export interface DenialReasonItem {
  reason: string;
  count: number;
  total_outstanding: number;
  percentage: number;
}

export interface PriorityDistributionItem {
  band: string;
  count: number;
  total_outstanding: number;
  expected_recovery: number;
  percentage: number;
}

export interface PolicyChunk {
  chunk_id: string;
  payer_id: string;
  payer_name: string;
  topic: string;
  title: string;
  content: string;
  required_documents?: string | null;
  filing_deadline_days: number;
  preferred_contact: string;
  similarity_score: number;
}

export interface RAGSearchResponse {
  query: string;
  payer_id?: string | null;
  results_count: number;
  chunks: PolicyChunk[];
}

export interface AgentDecision {
  claim_id: string;
  recommended_action: string;
  channel: string;
  urgency: string;
  confidence: number;
  reasoning: string;
  retrieved_policy_title: string;
  retrieved_policy_snippet: string;
  generated_message: string;
  filing_deadline_remaining_days: number;
  created_at: string;
}

export interface AgentActionItem {
  action_id: number;
  claim_id: string;
  recommended_action: string;
  reasoning: string;
  confidence?: number | null;
  retrieved_policy?: string | null;
  generated_message?: string | null;
  approval_status: string;
  created_at: string;
}

export interface GeneratedArtifacts {
  claim_id: string;
  patient_id: string;
  provider_id: string;
  payer_name: string;
  payer_id: string;
  denial_code?: string | null;
  denial_reason?: string | null;
  outstanding_amount: number;
  grounded_policy_title: string;
  grounded_policy_content: string;
  appeal_letter?: string | null;
  portal_message?: string | null;
  phone_script?: string | null;
  email_template?: string | null;
  edi_resubmission_note?: string | null;
}

export interface OutcomeProbabilityDistribution {
  p_approved_full: number;
  p_approved_partial: number;
  p_additional_info_required: number;
  p_denial_upheld: number;
}

export interface SimulationResultResponse {
  claim_id: string;
  payer_id: string;
  payer_name: string;
  action_type: string;
  channel: string;
  simulated_outcome: 'APPROVED_FULL' | 'APPROVED_PARTIAL' | 'ADDITIONAL_INFO_REQUIRED' | 'DENIAL_UPHELD' | string;
  recovered_amount: number;
  original_outstanding: number;
  remaining_outstanding: number;
  new_claim_status: string;
  turnaround_days: number;
  simulated_response_date: string;
  payer_response_text: string;
  remittance_reference: string;
  probability_distribution: OutcomeProbabilityDistribution;
  applied_to_db: boolean;
}

export interface BatchSimulationResponse {
  total_simulated: number;
  total_recovered: number;
  outcomes_breakdown: Record<string, number>;
  results: SimulationResultResponse[];
}

export interface ClaimLoopExecutionSummary {
  claim_id: string;
  patient_id: string;
  payer_id: string;
  payer_name: string;
  priority_score: number;
  priority_band: string;
  initial_status: string;
  chosen_action: string;
  chosen_channel: string;
  grounded_policy_title: string;
  simulated_outcome: string;
  original_outstanding: number;
  recovered_amount: number;
  final_outstanding: number;
  final_status: string;
  payer_response_snippet: string;
  remittance_reference: string;
}

export interface ClosedLoopRunResponse {
  run_id: string;
  timestamp: string;
  batch_size: number;
  total_processed: number;
  total_original_outstanding: number;
  total_recovered: number;
  recovery_yield_percentage: number;
  outcomes_breakdown: Record<string, number>;
  actions_breakdown: Record<string, number>;
  updated_dashboard_total_ar: number;
  updated_dashboard_recovered_revenue: number;
  results: ClaimLoopExecutionSummary[];
}

export interface ClosedLoopSummary {
  total_actions_executed: number;
  total_recovered_revenue: number;
  current_outstanding_ar: number;
  total_paid_claims: number;
}
