export interface ApiErrorShape {
  error?: string;
  detail?: string;
  message?: string;
}

export interface AccountProfile {
  account_id: number;
  email: string;
  subscription_level: string | null;
  story_security: string | null;
  allowed_classics_authors: string[] | null;
  created_at: string;
}

export interface AccountProfileUpdateInput {
  subscription_level: string;
  story_security: string;
  allowed_classics_authors: string[] | null;
}

export interface ParentPinStatusResponse {
  pin_enabled: boolean;
  verified: boolean;
  locked_until: string | null;
  attempts_remaining: number;
  session_expires_at: string | null;
}

export interface ParentPinSessionResponse extends ParentPinStatusResponse {
  status: string;
  session_token: string;
}

export interface ParentSummaryReader {
  reader_id: number;
  name: string | null;
  age: number | null;
  reading_level: string | null;
  trait_focus: string[];
  proficiency: string;
  stories_read: number;
  words_mastered: number;
  average_game_score: number | null;
  strengths: string[];
  focus_message: string | null;
  recommended_story_difficulty: number | null;
  recommended_vocabulary_difficulty: number | null;
  recommended_game_difficulty: number | null;
}

export interface ParentSummaryResponse {
  account_id: number;
  reader_count: number;
  aggregate_statistics: {
    stories_read: number;
    words_mastered: number;
    tracked_words: number;
    games_played: number;
    average_game_score: number | null;
  };
  readers: ParentSummaryReader[];
}

export interface GoalProgressResponse {
  current_value: number;
  target_value: number;
  progress_percent: number;
  status: string;
  updated_at: string | null;
  completed_at: string | null;
}

export interface GoalResponse {
  goal_id: number;
  reader_id: number;
  goal_type: string;
  title: string;
  target_value: number;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
  progress: GoalProgressResponse;
}

export interface ParentGoalsReaderSummary {
  reader_id: number;
  name: string | null;
  reading_level: string | null;
  proficiency: string;
  goals: GoalResponse[];
}

export interface ParentGoalsResponse {
  account_id: number;
  active_goal_count: number;
  completed_goal_count: number;
  readers: ParentGoalsReaderSummary[];
}

export interface ReaderGoalsResponse {
  reader: {
    reader_id: number;
    name: string | null;
    reading_level: string | null;
  };
  goals: GoalResponse[];
}

export interface ParentAnalyticsReader {
  reader_id: number;
  name: string | null;
  reading_level: string | null;
  proficiency: string;
  stories_read: number;
  words_mastered: number;
  average_game_score: number | null;
  strengths: string[];
  focus_areas: AnalyticsFocusArea[];
  recommendations: {
    recommended_story_difficulty: number;
    recommended_vocabulary_difficulty: number;
    recommended_game_difficulty: number;
  };
  game_practice: GamePracticeSummary;
  goals: GoalResponse[];
}

export interface GamePracticeAccuracyByType {
  game_type: string;
  sessions_played: number;
  words_attempted: number;
  words_correct: number;
  success_rate: number | null;
}

export interface RepeatedMissedWord {
  word_text: string;
  miss_count: number;
}

export interface GamePracticeSummary {
  sessions_total: number;
  sessions_this_week: number;
  words_practiced: number;
  words_correct: number;
  average_success_rate: number | null;
  practice_time_seconds: number;
  strongest_game_type: string | null;
  weakest_game_type: string | null;
  improvement_trend: string;
  accuracy_by_game_type: GamePracticeAccuracyByType[];
  repeated_missed_words: RepeatedMissedWord[];
}

export interface ParentAnalyticsResponse {
  account_id: number;
  reader_count: number;
  aggregate_statistics: {
    stories_read: number;
    words_mastered: number;
    tracked_words: number;
    games_played: number;
    average_game_score: number | null;
  };
  aggregate_game_practice: GamePracticeSummary;
  goal_summary: {
    active_goal_count: number;
    completed_goal_count: number;
  };
  readers: ParentAnalyticsReader[];
}

export interface ParentReaderWorkspaceResponse {
  reader: Reader;
  dashboard: ReaderDashboardData;
  learning_insights: ReaderLearningInsights;
  library_summary: {
    bookshelf_id: number;
    story_count: number;
    recent_stories: LibraryStory[];
  };
  world_summary: {
    world_count: number;
    worlds: Array<{
      reader_world_id: number;
      world_id: number | null;
      custom_name: string | null;
      name: string | null;
      description: string | null;
    }>;
  };
}

export interface ReaderHomeSummaryResponse {
  reader: {
    reader_id: number;
    name: string | null;
    age: number | null;
    reading_level: string | null;
    trait_focus: unknown;
  };
  continue_reading: LibraryStory | null;
  library_summary: {
    story_count: number;
    world_count: number;
  };
  vocabulary_summary: {
    tracked_words: number;
    practice_words: number;
    mastered_words: number;
    recommended_word: ReaderVocabularyItem | null;
  };
  game_summary: {
    recent_game: GameHistoryItem | null;
    recommended_game_difficulty: number;
    games_played_recently: number;
  };
  reader_path: {
    proficiency: string;
    recommended_story_difficulty: number;
    goal_message: string;
  };
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  status: string;
}

export interface ResetRequestResponse {
  status: string;
}

export interface ResetConfirmResponse {
  status: string;
}

export interface Reader {
  reader_id: number;
  account_id: number;
  name: string | null;
  age: number | null;
  reading_level: string | null;
  gender_preference: string | null;
  trait_focus: unknown;
  created_at: string | null;
}

export interface ReaderInput {
  name: string;
  age: number;
  reading_level: string;
  gender_preference: string;
  trait_focus: unknown;
}

export interface ReaderMutationResponse {
  reader_id: number;
  status: string;
}

export interface World {
  world_id: number;
  name: string | null;
  description: string | null;
  default_world: boolean | null;
}

export interface ReaderWorld {
  reader_world_id: number;
  reader_id: number | null;
  world_id: number | null;
  custom_name: string | null;
  created_at: string | null;
  world: World;
}

export interface AssignWorldResponse {
  reader_world_id: number;
  status: string;
}

export interface WorldRule {
  rule_id: number;
  world_id: number;
  rule_type: string | null;
  rule_description: string | null;
  created_at: string | null;
}

export interface Location {
  location_id: number;
  world_id: number | null;
  name: string | null;
  description: string | null;
}

export interface Character {
  character_id: number;
  world_id: number | null;
  name: string | null;
  species: string | null;
  personality_traits: unknown;
  home_location: number | null;
  updated_at: string | null;
}

export interface CharacterRelationship {
  relationship_id: number;
  character_a: number | null;
  character_b: number | null;
  relationship_type: string | null;
  relationship_strength: number | null;
  last_interaction: string | null;
}

export interface WorldDetailsResponse {
  world: World;
  locations: Location[];
  characters: Character[];
  relationships: CharacterRelationship[];
  world_rules: WorldRule[];
}

export interface CharacterCanonOverviewItem {
  character_id: number;
  name: string | null;
  species: string | null;
  personality_traits: unknown;
  home_location: number | null;
  canon_status: string;
  canon_version: number | null;
  is_locked: boolean;
  is_major_character: boolean;
  last_reviewed_at: string | null;
  enhanced_at: string | null;
}

export interface CharacterCanonOverviewResponse {
  reader_id: number;
  world_id: number;
  reader_world_id: number;
  world: {
    world_id: number;
    name: string | null;
    description: string | null;
  };
  characters: CharacterCanonOverviewItem[];
}

export interface CharacterCanonDetailResponse {
  reader_id: number;
  world_id: number;
  reader_world_id: number;
  world: {
    world_id: number;
    name: string | null;
    description: string | null;
  };
  character: {
    character_id: number;
    world_id: number | null;
    name: string | null;
    species: string | null;
    personality_traits: unknown;
    home_location: number | null;
  };
  canon: Record<string, unknown>;
  relationships: Array<Record<string, unknown>>;
  world_rules: Array<Record<string, unknown>>;
  recent_memory_events: Array<Record<string, unknown>>;
  history: Array<Record<string, unknown>>;
  enhancement_runs: Array<Record<string, unknown>>;
}

export interface CharacterCanonPreviewResponse {
  enhancement_run: Record<string, unknown>;
  preview_profile: Record<string, unknown>;
}

export interface CreateWorldLocationInput {
  name: string;
  description: string | null;
}

export interface CreateWorldCharacterInput {
  name: string;
  species: string;
  personality_traits: string[] | string;
  home_location: number | null;
}

export interface CreateWorldRelationshipInput {
  character_a: number;
  character_b: number;
  relationship_type: string;
  relationship_strength: number;
}

export interface StoryGenerateResponse {
  story_id: number;
  title: string;
  summary: string;
}

export interface DashboardReadingStatistics {
  stories_read: number | null;
  words_mastered: number | null;
  reading_speed: number | null;
  preferred_themes: unknown;
  traits_reinforced: unknown;
}

export interface DashboardRecentStory {
  story_id: number;
  title: string | null;
  created_at: string | null;
}

export interface DashboardVocabularyProgress {
  word: string | null;
  difficulty_level: number | null;
  mastery_level: number | null;
  last_seen: string | null;
}

export interface DashboardGameResult {
  game_type: string | null;
  difficulty_level: number | null;
  score: number | null;
  duration_seconds: number | null;
  played_at: string | null;
}

export interface ReaderDashboardData {
  reader_id: number;
  name: string | null;
  age: number | null;
  reading_level: string | null;
  trait_focus: unknown;
  reading_statistics: DashboardReadingStatistics;
  recent_stories: DashboardRecentStory[];
  vocabulary_progress: DashboardVocabularyProgress[];
  game_results: DashboardGameResult[];
}

export interface AccountDashboardData {
  account_id: number;
  readers: ReaderDashboardData[];
}

export interface AdaptiveProfile {
  reader_id: number;
  reading_level: string | null;
  stories_read: number | null;
  words_mastered: number | null;
  reading_speed: number | null;
  proficiency: string;
  recommended_story_difficulty: number;
  recommended_vocabulary_difficulty: number;
  recommended_game_difficulty: number;
}

export interface AdaptiveRecommendedWord {
  word_id: number;
  word: string | null;
  difficulty_level: number | null;
  mastery_level: number | null;
  last_seen: string | null;
}

export interface AdaptiveRecommendations {
  recommended_words: AdaptiveRecommendedWord[];
  recommended_story_parameters: unknown;
  recommended_game_difficulty: number;
}

export interface AnalyticsFocusArea {
  category: string;
  priority: number;
  message: string;
}

export interface ReaderLearningInsights {
  reader_id: number;
  name: string | null;
  age: number | null;
  reading_level: string | null;
  trait_focus: unknown;
  proficiency: string;
  reading_summary: {
    stories_read: number;
    words_mastered: number;
    reading_speed: number | null;
    preferred_themes: unknown;
    traits_reinforced: unknown;
  };
  story_summary: {
    recent_story_count: number;
    latest_story_title: string | null;
    latest_story_at: string | null;
  };
  vocabulary_summary: {
    tracked_words: number;
    mastered_words: number;
    developing_words: number;
    needs_practice_words: number;
    recent_words: AdaptiveRecommendedWord[];
  };
  game_summary: {
    total_games_played: number;
    average_score: number | null;
    average_duration_seconds: number | null;
    strongest_game_type: string | null;
    most_recent_game_type: string | null;
    most_recent_game_at: string | null;
  };
  recommendations: {
    recommended_story_difficulty: number;
    recommended_vocabulary_difficulty: number;
    recommended_game_difficulty: number;
  };
  strengths: string[];
  focus_areas: AnalyticsFocusArea[];
}

export interface AccountLearningInsights {
  account_id: number;
  reader_count: number;
  aggregate_statistics: {
    stories_read: number;
    words_mastered: number;
    tracked_words: number;
    games_played: number;
    average_game_score: number | null;
  };
  readers: Array<{
    reader_id: number;
    name: string | null;
    reading_level: string | null;
    proficiency: string;
    stories_read: number;
    words_mastered: number;
    average_game_score: number | null;
    strengths: string[];
    focus_areas: AnalyticsFocusArea[];
    recommendations: {
      recommended_story_difficulty: number;
      recommended_vocabulary_difficulty: number;
      recommended_game_difficulty: number;
    };
  }>;
}

export interface ClassicsCover {
  mode: string;
  image_url: string | null;
  accent_token?: string | null;
  display_title?: string | null;
}

export interface ShelfItem {
  story_id: number;
  title: string | null;
  source_author: string | null;
  age_range: string | null;
  reading_level: string | null;
  preview_text: string;
  cover: ClassicsCover;
  immersive_reader_available: boolean;
  narration_available: boolean;
}

export interface ShelfGroup {
  author: string;
  items: ShelfItem[];
}

export interface ClassicsShelfResponse {
  groups: ShelfGroup[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface ClassicsDiscoveryResponse {
  items: ShelfItem[];
  total_count: number;
  limit: number;
  offset: number;
  query: string | null;
  applied_author: string | null;
  match_mode: string;
  prompt_examples: string[];
}

export interface GuestLimitsResponse {
  session_token: string;
  expires_at: string | null;
  classics_read_limit: number;
  classics_reads_used: number;
  classics_reads_remaining: number;
  game_launch_limit: number;
  game_launches_used: number;
  game_launches_remaining: number;
}

export interface GuestSessionStartResponse extends GuestLimitsResponse {
  status: string;
}

export interface ClassicStoryDetail {
  story_id: number;
  title: string | null;
  source_author: string | null;
  source_story_id: number | null;
  age_range: string | null;
  reading_level: string | null;
  moral: string | null;
  characters: unknown;
  locations: unknown;
  traits: unknown;
  themes: unknown;
  cover: ClassicsCover;
  summary: string;
  immersive_reader_available: boolean;
}

export interface ClassicReadUnit {
  unit_id: string;
  unit_order: number;
  unit_type: string;
  scene_title: string | null;
  text: string;
  narration_text: string | null;
  audio_start_ms: number | null;
  audio_end_ms: number | null;
  speech_marks: Array<{
    time: number | null;
    type: string | null;
    start: number | null;
    end: number | null;
    value: string | null;
  }>;
  illustration: {
    mode: string;
    image_url: string | null;
    prompt_excerpt: string | null;
  };
}

export interface ClassicReadResponse {
  story_id: number;
  title: string | null;
  source_author: string | null;
  age_range: string | null;
  reading_level: string | null;
  cover: ClassicsCover;
  reader_mode: string;
  has_scene_groups: boolean;
  has_paragraphs: boolean;
  has_narration_text: boolean;
  audio_url: string | null;
  voice: string | null;
  generated_at: string | null;
  narration_available: boolean;
  units: ClassicReadUnit[];
  moral: string | null;
  characters: unknown;
  locations: unknown;
  traits: unknown;
  themes: unknown;
  guest_limits?: GuestLimitsResponse;
}

export interface GuestGamesCatalogResponse {
  game_type: string;
  description: string;
  stories: ShelfItem[];
}

export interface GuestGamePreviewResponse {
  game_type: string;
  story_id: number;
  story_title: string | null;
  source_author: string | null;
  preview_text: string;
  payload: Record<string, unknown>;
  guest_limits: GuestLimitsResponse;
}

export interface LibraryStory {
  story_id: number;
  title: string | null;
  trait_focus: string | null;
  current_version: number | null;
  created_at: string | null;
  updated_at: string | null;
  reader_world_id: number | null;
  world_id: number | null;
  world_name: string | null;
  custom_world_name: string | null;
  published: boolean;
  epub_url: string | null;
  epub_created_at: string | null;
  cover_image_url: string | null;
  narration_available: boolean;
  artwork_available: boolean;
}

export interface ReaderLibraryResponse {
  reader_id: number;
  reader_name: string | null;
  bookshelf_id: number;
  bookshelf_created_at: string | null;
  story_count: number;
  stories: LibraryStory[];
}

export interface LibraryStoryDetailResponse {
  reader_id: number;
  reader_name: string | null;
  bookshelf_id: number;
  story: LibraryStory;
}

export interface PublishLibraryStoryResponse {
  status: string;
  story_id: number;
  epub_url: string;
  story: LibraryStory;
}

export interface StoryNarrationResponse {
  job_id: number;
  account_id: number;
  story_id: number;
  job_type: string;
  status: string;
  error_message: string | null;
  result_payload: {
    story_id?: number;
    scenes_narrated?: number;
    audio_files_created?: number;
  } | null;
  worker_id: string | null;
  attempt_count: number;
  created_at: string | null;
  updated_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  already_ready: boolean;
}

export interface StoryNarrationMetadata {
  scene_id: number | null;
  audio_url: string | null;
  speech_marks_json: unknown;
  voice: string | null;
  generated_at: string | null;
}

export interface StoryIllustrationResponse {
  job_id: number;
  account_id: number;
  story_id: number;
  job_type: string;
  status: string;
  error_message: string | null;
  result_payload: {
    story_id?: number;
    image_url?: string;
    scenes_illustrated?: number;
  } | null;
  worker_id: string | null;
  attempt_count: number;
  created_at: string | null;
  updated_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  already_ready: boolean;
}

export interface MediaJobStatus {
  job_id: number;
  account_id: number;
  story_id: number;
  job_type: string;
  status: string;
  error_message: string | null;
  result_payload: Record<string, unknown> | null;
  worker_id: string | null;
  attempt_count: number;
  created_at: string | null;
  updated_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  already_ready: boolean;
}

export interface StoryIllustrationMetadata {
  image_url: string;
}

export interface SceneIllustrationMetadata {
  scene_id: number;
  scene_order: number | null;
  image_url: string | null;
  prompt_used: string | null;
  generation_model: string | null;
  generated_at: string | null;
}

export interface V1GameCatalogItem {
  game_type: string;
  label: string;
  description: string;
  default_item_count: number;
  supports_story_source: boolean;
}

export interface V1GameCatalogRecentSession {
  session_id: number;
  game_type: string;
  completion_status: string;
  duration_seconds: number | null;
  started_at: string | null;
  ended_at: string | null;
}

export interface V1GameCatalogResponse {
  reader_id: number;
  recommended_difficulty: number;
  games: V1GameCatalogItem[];
  recent_sessions: V1GameCatalogRecentSession[];
}

export interface V1GameSessionWordItem {
  word_id: number | null;
  word: string;
  definition: string | null;
  example_sentence: string | null;
  difficulty_level: number | null;
  reader_id: number;
  story_id: number | null;
  source_type: string;
  trait_focus: string | null;
}

export interface V1GameSessionResponse {
  session_id: number;
  reader_id: number;
  game_type: string;
  source_type: string;
  source_story_id: number | null;
  difficulty_level: number;
  status: string;
  completion_status: string;
  started_at: string | null;
  items: V1GameSessionWordItem[];
  payload: Record<string, unknown>;
}

export interface V1GameWordAttempt {
  attempt_id: number;
  word_id: number | null;
  word_text: string;
  game_type: string;
  attempt_count: number;
  correct: boolean;
  time_spent_seconds: number;
  hint_used: boolean;
  skipped: boolean;
  created_at: string | null;
}

export interface V1GameSessionDetailResponse {
  session_id: number;
  reader_id: number;
  game_type: string;
  source_type: string;
  source_story_id: number | null;
  difficulty_level: number;
  status: string;
  item_count: number;
  words_attempted: number;
  words_correct: number;
  words_incorrect: number;
  hints_used: number;
  completion_status: string;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
  items: V1GameSessionWordItem[];
  payload: Record<string, unknown> | null;
  attempts: V1GameWordAttempt[];
}

export interface ReaderGamePracticeSummaryResponse extends GamePracticeSummary {}

export interface V1GameCompletionAttemptInput {
  word_id?: number | null;
  word_text: string;
  attempt_count: number;
  correct: boolean;
  time_spent_seconds: number;
  hint_used?: boolean;
  skipped?: boolean;
}

export interface V1GameSessionCompleteResponse {
  session_id: number;
  reader_id: number;
  game_type: string;
  difficulty_level: number;
  status: string;
  completion_status: string;
  words_attempted: number;
  words_correct: number;
  words_incorrect: number;
  hints_used: number;
  duration_seconds: number | null;
  legacy_game_result_id: number;
}

export interface GameHistoryItem {
  game_result_id: number;
  game_type: string | null;
  difficulty_level: number | null;
  score: number | null;
  duration_seconds: number | null;
  played_at: string | null;
}

export interface ReaderVocabularyItem {
  word_id: number;
  word: string | null;
  difficulty_level: number | null;
  mastery_level: number | null;
  last_seen: string | null;
}

export interface UpdateVocabularyProgressResponse {
  word_id: number;
  mastery_level: number | null;
  last_seen: string | null;
}

export interface GeneratedReadingScene {
  scene_id: number;
  scene_order: number | null;
  scene_text: string;
  illustration_url: string | null;
  audio_url: string | null;
  speech_marks_json: Array<{
    time?: number | null;
    type?: string | null;
    start?: number | null;
    end?: number | null;
    value?: string | null;
  }>;
}

export interface GeneratedStoryReadResponse {
  story_id: number;
  title: string | null;
  trait_focus: string | null;
  scenes: GeneratedReadingScene[];
}

export interface StoryMemoryEvent {
  event_id: number;
  characters: number[] | null;
  location_id: number | null;
  event_summary: string | null;
}

export interface SafetyEvaluationResponse {
  safety_score: number;
  classification: string;
  flags: string[];
  matched_terms: string[];
  account_story_security?: string | null;
}

export interface StorySceneSafetyResponse extends SafetyEvaluationResponse {
  scene_id: number;
  scene_order: number | null;
  scene_text: string;
}

export interface StoryEventSafetyResponse extends SafetyEvaluationResponse {
  event_id: number;
  event_summary: string;
}

export interface StorySafetyReportResponse extends SafetyEvaluationResponse {
  story_id: number;
  title: string | null;
  scenes: StorySceneSafetyResponse[];
  events: StoryEventSafetyResponse[];
}

export interface SceneSafetyReportResponse extends SafetyEvaluationResponse {
  story_id: number;
  scene_id: number;
  scene_order: number | null;
  scene_text: string;
}

export interface ContinuityResponse {
  continuity_valid: boolean;
  conflicts: string[];
}

export interface BlogPostSummary {
  post_id: number;
  slug: string;
  title: string;
  summary: string;
  cover_eyebrow: string | null;
  author_name: string;
  published_at: string | null;
  comment_count: number;
}

export interface BlogComment {
  comment_id: number;
  post_id: number;
  author_name: string;
  comment_body: string;
  moderation_status: string;
  moderation_notes: string | null;
  created_at: string | null;
  moderated_at: string | null;
}

export interface BlogPostDetail {
  post_id: number;
  slug: string;
  title: string;
  summary: string;
  body_text: string;
  cover_eyebrow: string | null;
  author_name: string;
  published_at: string | null;
  comments: BlogComment[];
}

export interface BlogCommentSubmissionResponse {
  status: string;
  comment_id: number;
}

export interface ContactSubmissionResponse {
  status: string;
  submission_id: number;
  delivery_status: string;
}

export interface ModerationComment {
  comment_id: number;
  post_id: number;
  post_title: string;
  post_slug: string;
  author_name: string;
  author_email: string;
  comment_body: string;
  moderation_status: string;
  moderation_notes: string | null;
  created_at: string | null;
  moderated_at: string | null;
}

export interface ContactSubmissionRecord {
  submission_id: number;
  name: string;
  email: string;
  subject: string;
  message: string;
  delivery_status: string;
  created_at: string | null;
  delivered_at: string | null;
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

function buildUrl(path: string): string {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

export function resolveApiAssetUrl(path: string | null | undefined): string | null {
  if (!path) {
    return null;
  }

  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  if (path.startsWith("/") && API_BASE_URL) {
    return `${API_BASE_URL}${path}`;
  }

  return path;
}

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers = new Headers(options.headers ?? {});

  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(buildUrl(path), {
    ...options,
    headers,
  });

  const raw = await response.text();
  let payload: unknown = null;

  if (raw) {
    try {
      payload = JSON.parse(raw) as unknown;
    } catch {
      payload = { detail: raw };
    }
  }

  if (!response.ok) {
    const errorPayload = (payload ?? {}) as ApiErrorShape;
    const code = errorPayload.error ?? "request_failed";
    const message = errorPayload.message ?? errorPayload.detail ?? `Request failed with status ${response.status}`;
    throw new ApiError(response.status, code, message);
  }

  return payload as T;
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function registerAccount(email: string, password: string): Promise<RegisterResponse> {
  return request<RegisterResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function requestPasswordReset(email: string): Promise<ResetRequestResponse> {
  return request<ResetRequestResponse>("/auth/reset-request", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function confirmPasswordReset(resetToken: string, newPassword: string): Promise<ResetConfirmResponse> {
  return request<ResetConfirmResponse>("/auth/reset-confirm", {
    method: "POST",
    body: JSON.stringify({ reset_token: resetToken, new_password: newPassword }),
  });
}

export function getMe(token: string): Promise<AccountProfile> {
  return request<AccountProfile>("/accounts/me", {}, token);
}

export function updateMe(payload: AccountProfileUpdateInput, token: string): Promise<AccountProfile> {
  return request<AccountProfile>(
    "/accounts/me",
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function getParentPinStatus(token: string, sessionToken?: string | null): Promise<ParentPinStatusResponse> {
  return request<ParentPinStatusResponse>(
    "/parent/pin/status",
    {
      headers: sessionToken ? { "X-Parent-Pin-Session": sessionToken } : undefined,
    },
    token,
  );
}

export function setParentPin(pin: string, token: string, sessionToken?: string | null): Promise<ParentPinSessionResponse> {
  return request<ParentPinSessionResponse>(
    "/parent/pin/set",
    {
      method: "POST",
      headers: sessionToken ? { "X-Parent-Pin-Session": sessionToken } : undefined,
      body: JSON.stringify({ pin }),
    },
    token,
  );
}

export function verifyParentPin(pin: string, token: string): Promise<ParentPinSessionResponse> {
  return request<ParentPinSessionResponse>(
    "/parent/pin/verify",
    {
      method: "POST",
      body: JSON.stringify({ pin }),
    },
    token,
  );
}

export function clearParentPinSession(token: string, sessionToken: string): Promise<{ status: string }> {
  return request<{ status: string }>(
    "/parent/pin/session",
    {
      method: "DELETE",
      headers: { "X-Parent-Pin-Session": sessionToken },
    },
    token,
  );
}

export function getParentSummary(token: string): Promise<ParentSummaryResponse> {
  return request<ParentSummaryResponse>("/parent/summary", {}, token);
}

export function getParentAnalytics(token: string): Promise<ParentAnalyticsResponse> {
  return request<ParentAnalyticsResponse>("/parent/analytics", {}, token);
}

export function getParentGoals(token: string): Promise<ParentGoalsResponse> {
  return request<ParentGoalsResponse>("/parent/goals", {}, token);
}

export function createReaderGoal(
  readerId: number,
  payload: { goal_type: string; target_value: number; title?: string | null },
  token: string,
): Promise<GoalResponse> {
  return request<GoalResponse>(
    `/parent/readers/${readerId}/goals`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function updateParentGoal(
  goalId: number,
  payload: { title?: string | null; target_value: number; is_active: boolean },
  token: string,
): Promise<GoalResponse> {
  return request<GoalResponse>(
    `/parent/goals/${goalId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function getParentReaderSummary(readerId: number, token: string): Promise<ParentReaderWorkspaceResponse> {
  return request<ParentReaderWorkspaceResponse>(`/parent/readers/${readerId}/summary`, {}, token);
}

export function getReaderHomeSummary(readerId: number, token: string): Promise<ReaderHomeSummaryResponse> {
  return request<ReaderHomeSummaryResponse>(`/readers/${readerId}/home`, {}, token);
}

export function getReaderGoals(readerId: number, token: string): Promise<ReaderGoalsResponse> {
  return request<ReaderGoalsResponse>(`/readers/${readerId}/goals`, {}, token);
}

export function getReaders(token: string): Promise<Reader[]> {
  return request<Reader[]>("/readers", {}, token);
}

export function getAccountDashboard(accountId: number, token: string): Promise<AccountDashboardData> {
  return request<AccountDashboardData>(`/accounts/${accountId}/dashboard`, {}, token);
}

export function getReaderDashboard(readerId: number, token: string): Promise<ReaderDashboardData> {
  return request<ReaderDashboardData>(`/readers/${readerId}/dashboard`, {}, token);
}

export function getAdaptiveProfile(readerId: number, token: string): Promise<AdaptiveProfile> {
  return request<AdaptiveProfile>(`/readers/${readerId}/adaptive-profile`, {}, token);
}

export function getAdaptiveRecommendations(readerId: number, token: string): Promise<AdaptiveRecommendations> {
  return request<AdaptiveRecommendations>(`/readers/${readerId}/recommendations`, {}, token);
}

export function getAccountLearningInsights(accountId: number, token: string): Promise<AccountLearningInsights> {
  return request<AccountLearningInsights>(`/accounts/${accountId}/learning-insights`, {}, token);
}

export function getReaderLearningInsights(readerId: number, token: string): Promise<ReaderLearningInsights> {
  return request<ReaderLearningInsights>(`/readers/${readerId}/learning-insights`, {}, token);
}

export function getWorlds(): Promise<World[]> {
  return request<World[]>("/worlds");
}

export function getWorldDetails(readerId: number, worldId: number, token: string): Promise<WorldDetailsResponse> {
  return request<WorldDetailsResponse>(`/readers/${readerId}/worlds/${worldId}/details`, {}, token);
}

export function getCharacterCanonOverview(
  readerId: number,
  worldId: number,
  token: string,
): Promise<CharacterCanonOverviewResponse> {
  return request<CharacterCanonOverviewResponse>(`/readers/${readerId}/worlds/${worldId}/characters/canon`, {}, token);
}

export function getCharacterCanonDetail(
  readerId: number,
  worldId: number,
  characterId: number,
  token: string,
): Promise<CharacterCanonDetailResponse> {
  return request<CharacterCanonDetailResponse>(
    `/readers/${readerId}/worlds/${worldId}/characters/${characterId}/canon`,
    {},
    token,
  );
}

export function enhanceCharacterCanonPreview(
  readerId: number,
  worldId: number,
  characterId: number,
  payload: { section_mode: "full" | "narrative" | "visual" },
  token: string,
): Promise<CharacterCanonPreviewResponse> {
  return request<CharacterCanonPreviewResponse>(
    `/readers/${readerId}/worlds/${worldId}/characters/${characterId}/canon/enhance-preview`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function saveCharacterCanon(
  readerId: number,
  worldId: number,
  characterId: number,
  payload: { updates: Record<string, unknown>; enhancement_run_id?: number | null },
  token: string,
): Promise<CharacterCanonDetailResponse> {
  return request<CharacterCanonDetailResponse>(
    `/readers/${readerId}/worlds/${worldId}/characters/${characterId}/canon`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function publishCharacterCanon(
  readerId: number,
  worldId: number,
  characterId: number,
  payload: { updates: Record<string, unknown>; enhancement_run_id?: number | null },
  token: string,
): Promise<CharacterCanonDetailResponse> {
  return request<CharacterCanonDetailResponse>(
    `/readers/${readerId}/worlds/${worldId}/characters/${characterId}/canon/publish`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function createReaderWorldLocation(
  readerId: number,
  worldId: number,
  payload: CreateWorldLocationInput,
  token: string,
): Promise<Location> {
  return request<Location>(
    `/readers/${readerId}/worlds/${worldId}/locations`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function createReaderWorldCharacter(
  readerId: number,
  worldId: number,
  payload: CreateWorldCharacterInput,
  token: string,
): Promise<Character> {
  return request<Character>(
    `/readers/${readerId}/worlds/${worldId}/characters`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function createReaderWorldRelationship(
  readerId: number,
  worldId: number,
  payload: CreateWorldRelationshipInput,
  token: string,
): Promise<CharacterRelationship> {
  return request<CharacterRelationship>(
    `/readers/${readerId}/worlds/${worldId}/relationships`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function getReaderWorlds(readerId: number, token: string): Promise<ReaderWorld[]> {
  return request<ReaderWorld[]>(`/readers/${readerId}/worlds`, {}, token);
}

export function assignWorldToReader(
  readerId: number,
  payload: { world_id?: number; custom_name?: string | null },
  token: string,
): Promise<AssignWorldResponse> {
  return request<AssignWorldResponse>(
    `/readers/${readerId}/worlds`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function generateStoryForReader(
  payload: { reader_id: number; world_id: number; theme: string; target_length: string },
  token: string,
): Promise<StoryGenerateResponse> {
  return request<StoryGenerateResponse>(
    "/stories/generate",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function createReader(payload: ReaderInput, token: string): Promise<ReaderMutationResponse> {
  return request<ReaderMutationResponse>(
    "/readers",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function updateReader(readerId: number, payload: ReaderInput, token: string): Promise<Reader> {
  return request<Reader>(
    `/readers/${readerId}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function deleteReader(readerId: number, token: string): Promise<{ status: string }> {
  return request<{ status: string }>(
    `/readers/${readerId}`,
    {
      method: "DELETE",
    },
    token,
  );
}

export function getReaderLibrary(readerId: number, token: string): Promise<ReaderLibraryResponse> {
  return request<ReaderLibraryResponse>(`/readers/${readerId}/library`, {}, token);
}

export function getLibraryStoryDetail(
  readerId: number,
  storyId: number,
  token: string,
): Promise<LibraryStoryDetailResponse> {
  return request<LibraryStoryDetailResponse>(`/readers/${readerId}/library/${storyId}`, {}, token);
}

export function publishLibraryStory(
  readerId: number,
  storyId: number,
  token: string,
): Promise<PublishLibraryStoryResponse> {
  return request<PublishLibraryStoryResponse>(
    `/readers/${readerId}/library/${storyId}/publish`,
    {
      method: "POST",
    },
    token,
  );
}

export function getGeneratedStoryRead(storyId: number, token: string): Promise<GeneratedStoryReadResponse> {
  return request<GeneratedStoryReadResponse>(`/stories/${storyId}/read`, {}, token);
}

export function narrateGeneratedStory(storyId: number, token: string): Promise<StoryNarrationResponse> {
  return request<StoryNarrationResponse>(
    `/stories/${storyId}/narrate`,
    {
      method: "POST",
    },
    token,
  );
}

export function getGeneratedStoryNarration(storyId: number, token: string): Promise<StoryNarrationMetadata[]> {
  return request<StoryNarrationMetadata[]>(`/stories/${storyId}/narration`, {}, token);
}

export function illustrateGeneratedStory(storyId: number, token: string): Promise<StoryIllustrationResponse> {
  return request<StoryIllustrationResponse>(
    `/stories/${storyId}/illustrate`,
    {
      method: "POST",
    },
    token,
  );
}

export function getGeneratedStoryIllustration(storyId: number, token: string): Promise<StoryIllustrationMetadata> {
  return request<StoryIllustrationMetadata>(`/stories/${storyId}/illustration`, {}, token);
}

export function getGeneratedStoryIllustrations(storyId: number, token: string): Promise<SceneIllustrationMetadata[]> {
  return request<SceneIllustrationMetadata[]>(`/stories/${storyId}/illustrations`, {}, token);
}

export function getMediaJob(jobId: number, token: string): Promise<MediaJobStatus> {
  return request<MediaJobStatus>(`/media-jobs/${jobId}`, {}, token);
}

export function getLatestStoryMediaJob(
  storyId: number,
  jobType: string,
  token: string,
): Promise<MediaJobStatus | null> {
  return request<MediaJobStatus | null>(`/stories/${storyId}/media-jobs/${jobType}/latest`, {}, token);
}

export function getStoryMemory(storyId: number, token?: string | null): Promise<StoryMemoryEvent[]> {
  return request<StoryMemoryEvent[]>(`/stories/${storyId}/memory`, {}, token);
}

export function getReaderWorldHistory(
  readerId: number,
  worldId: number,
  token: string,
): Promise<StoryMemoryEvent[]> {
  return request<StoryMemoryEvent[]>(`/readers/${readerId}/worlds/${worldId}/history`, {}, token);
}

export function getCharacterHistory(characterId: number, token?: string | null): Promise<StoryMemoryEvent[]> {
  return request<StoryMemoryEvent[]>(`/characters/${characterId}/history`, {}, token);
}

export function getReaderWorldCharacterHistory(
  readerId: number,
  worldId: number,
  characterId: number,
  token: string,
): Promise<StoryMemoryEvent[]> {
  return request<StoryMemoryEvent[]>(
    `/readers/${readerId}/worlds/${worldId}/characters/${characterId}/history`,
    {},
    token,
  );
}

export function getWorldHistory(worldId: number, token?: string | null): Promise<StoryMemoryEvent[]> {
  return request<StoryMemoryEvent[]>(`/worlds/${worldId}/history`, {}, token);
}

export function checkTextSafety(text: string, token: string): Promise<SafetyEvaluationResponse> {
  return request<SafetyEvaluationResponse>(
    "/safety/text-check",
    {
      method: "POST",
      body: JSON.stringify({ text }),
    },
    token,
  );
}

export function getStorySafetyReport(storyId: number, token: string): Promise<StorySafetyReportResponse> {
  return request<StorySafetyReportResponse>(`/stories/${storyId}/safety-report`, {}, token);
}

export function getSceneSafetyReport(storyId: number, sceneId: number, token: string): Promise<SceneSafetyReportResponse> {
  return request<SceneSafetyReportResponse>(`/stories/${storyId}/scenes/${sceneId}/safety-report`, {}, token);
}

export function checkStoryContinuity(
  storyId: number,
  worldId: number,
  storySummary: string,
  token?: string | null,
): Promise<ContinuityResponse> {
  return request<ContinuityResponse>(
    "/continuity/story-check",
    {
      method: "POST",
      body: JSON.stringify({ story_id: storyId, world_id: worldId, story_summary: storySummary }),
    },
    token,
  );
}

export function checkCharacterContinuity(
  characterId: number,
  worldId: number,
  storySummary: string,
  token?: string | null,
): Promise<ContinuityResponse> {
  return request<ContinuityResponse>(
    "/continuity/character-check",
    {
      method: "POST",
      body: JSON.stringify({ character_id: characterId, world_id: worldId, story_summary: storySummary }),
    },
    token,
  );
}

export function checkReaderWorldStoryContinuity(
  readerId: number,
  worldId: number,
  storyId: number,
  storySummary: string,
  token: string,
): Promise<ContinuityResponse> {
  return request<ContinuityResponse>(
    `/continuity/readers/${readerId}/worlds/${worldId}/stories/${storyId}/check`,
    {
      method: "POST",
      body: JSON.stringify({ story_summary: storySummary }),
    },
    token,
  );
}

export function checkReaderWorldContinuity(
  readerId: number,
  worldId: number,
  storySummary: string,
  token: string,
): Promise<ContinuityResponse> {
  return request<ContinuityResponse>(
    `/continuity/readers/${readerId}/worlds/${worldId}/check`,
    {
      method: "POST",
      body: JSON.stringify({ story_summary: storySummary }),
    },
    token,
  );
}

export function checkReaderWorldCharacterContinuity(
  readerId: number,
  worldId: number,
  characterId: number,
  storySummary: string,
  token: string,
): Promise<ContinuityResponse> {
  return request<ContinuityResponse>(
    `/continuity/readers/${readerId}/worlds/${worldId}/characters/${characterId}/check`,
    {
      method: "POST",
      body: JSON.stringify({ story_summary: storySummary }),
    },
    token,
  );
}

export function checkWorldContinuity(worldId: number, storySummary: string, token?: string | null): Promise<ContinuityResponse> {
  return request<ContinuityResponse>(
    "/continuity/world-check",
    {
      method: "POST",
      body: JSON.stringify({ world_id: worldId, story_summary: storySummary }),
    },
    token,
  );
}

export function getReaderGameCatalog(readerId: number, token: string): Promise<V1GameCatalogResponse> {
  return request<V1GameCatalogResponse>(`/readers/${readerId}/games/catalog`, {}, token);
}

export function createReaderGameSession(
  readerId: number,
  payload: {
    game_type: string;
    story_id?: number | null;
    source_type?: string | null;
    difficulty_level?: number | null;
    item_count?: number | null;
  },
  token: string,
): Promise<V1GameSessionResponse> {
  return request<V1GameSessionResponse>(
    `/readers/${readerId}/games/sessions`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function getReaderGameSession(
  readerId: number,
  sessionId: number,
  token: string,
): Promise<V1GameSessionDetailResponse> {
  return request<V1GameSessionDetailResponse>(`/readers/${readerId}/games/sessions/${sessionId}`, {}, token);
}

export function getReaderGamePracticeSummary(
  readerId: number,
  token: string,
): Promise<ReaderGamePracticeSummaryResponse> {
  return request<ReaderGamePracticeSummaryResponse>(`/readers/${readerId}/games/summary`, {}, token);
}

export function completeReaderGameSession(
  readerId: number,
  sessionId: number,
  payload: {
    completion_status: string;
    duration_seconds: number;
    attempts: V1GameCompletionAttemptInput[];
  },
  token: string,
): Promise<V1GameSessionCompleteResponse> {
  return request<V1GameSessionCompleteResponse>(
    `/readers/${readerId}/games/sessions/${sessionId}/complete`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function getReaderGameHistory(readerId: number, token: string, limit = 20): Promise<GameHistoryItem[]> {
  return request<GameHistoryItem[]>(`/readers/${readerId}/games/history?limit=${limit}`, {}, token);
}

export function getReaderVocabulary(readerId: number, token: string): Promise<ReaderVocabularyItem[]> {
  return request<ReaderVocabularyItem[]>(`/readers/${readerId}/vocabulary`, {}, token);
}

export function getReaderPracticeVocabulary(readerId: number, token: string): Promise<ReaderVocabularyItem[]> {
  return request<ReaderVocabularyItem[]>(`/readers/${readerId}/vocabulary/practice`, {}, token);
}

export function updateReaderVocabularyProgress(
  readerId: number,
  wordId: number,
  masteryLevel: number,
  token: string,
): Promise<UpdateVocabularyProgressResponse> {
  return request<UpdateVocabularyProgressResponse>(
    `/readers/${readerId}/vocabulary/${wordId}/progress`,
    {
      method: "POST",
      body: JSON.stringify({ mastery_level: masteryLevel }),
    },
    token,
  );
}

export function getClassicsShelf(params: { author?: string; q?: string; limit?: number; offset?: number }) {
  const search = new URLSearchParams();
  if (params.author) {
    search.set("author", params.author);
  }
  if (params.q) {
    search.set("q", params.q);
  }
  if (params.limit) {
    search.set("limit", String(params.limit));
  }
  if (params.offset) {
    search.set("offset", String(params.offset));
  }
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request<ClassicsShelfResponse>(`/classics/shelf${suffix}`);
}

export function getClassicsDiscovery(params: { author?: string; q?: string; limit?: number; offset?: number }) {
  const search = new URLSearchParams();
  if (params.author) {
    search.set("author", params.author);
  }
  if (params.q) {
    search.set("q", params.q);
  }
  if (params.limit) {
    search.set("limit", String(params.limit));
  }
  if (params.offset) {
    search.set("offset", String(params.offset));
  }
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request<ClassicsDiscoveryResponse>(`/classics/discover${suffix}`);
}

export function getClassicStory(storyId: number) {
  return request<ClassicStoryDetail>(`/classics/stories/${storyId}`);
}

export function getClassicRead(storyId: number) {
  return request<ClassicReadResponse>(`/classics/stories/${storyId}/read`);
}

export function startGuestSession(existingSessionToken?: string | null) {
  return request<GuestSessionStartResponse>(
    "/guest/session/start",
    {
      method: "POST",
      body: JSON.stringify({ existing_session_token: existingSessionToken ?? null }),
    },
  );
}

export function getGuestLimits(sessionToken: string) {
  return request<GuestLimitsResponse>(
    "/guest/limits",
    {
      headers: { "X-Guest-Session": sessionToken },
    },
  );
}

export function getGuestClassics(params: { author?: string; q?: string; limit?: number; offset?: number }) {
  const search = new URLSearchParams();
  if (params.author) {
    search.set("author", params.author);
  }
  if (params.q) {
    search.set("q", params.q);
  }
  if (params.limit) {
    search.set("limit", String(params.limit));
  }
  if (params.offset) {
    search.set("offset", String(params.offset));
  }
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request<ClassicsShelfResponse>(`/guest/classics${suffix}`);
}

export function getGuestClassicsDiscovery(params: { author?: string; q?: string; limit?: number; offset?: number }) {
  const search = new URLSearchParams();
  if (params.author) {
    search.set("author", params.author);
  }
  if (params.q) {
    search.set("q", params.q);
  }
  if (params.limit) {
    search.set("limit", String(params.limit));
  }
  if (params.offset) {
    search.set("offset", String(params.offset));
  }
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request<ClassicsDiscoveryResponse>(`/guest/classics/discover${suffix}`);
}

export function getGuestClassicStory(storyId: number) {
  return request<ClassicStoryDetail>(`/guest/classics/stories/${storyId}`);
}

export function getGuestClassicRead(storyId: number, sessionToken: string) {
  return request<ClassicReadResponse>(
    `/guest/classics/stories/${storyId}/read`,
    {
      headers: { "X-Guest-Session": sessionToken },
    },
  );
}

export function getGuestGamesCatalog() {
  return request<GuestGamesCatalogResponse>("/guest/games");
}

export function launchGuestGamePreview(
  sessionToken: string,
  payload: { story_id: number; item_count?: number | null },
) {
  return request<GuestGamePreviewResponse>(
    "/guest/games/preview-session",
    {
      method: "POST",
      headers: { "X-Guest-Session": sessionToken },
      body: JSON.stringify(payload),
    },
  );
}

export function getBlogPosts(): Promise<BlogPostSummary[]> {
  return request<BlogPostSummary[]>("/blog/posts");
}

export function getBlogPost(slug: string): Promise<BlogPostDetail> {
  return request<BlogPostDetail>(`/blog/posts/${slug}`);
}

export function submitBlogComment(
  postId: number,
  payload: { author_name: string; author_email: string; comment_body: string },
): Promise<BlogCommentSubmissionResponse> {
  return request<BlogCommentSubmissionResponse>(
    `/blog/posts/${postId}/comments`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function submitContactForm(payload: {
  name: string;
  email: string;
  subject: string;
  message: string;
}): Promise<ContactSubmissionResponse> {
  return request<ContactSubmissionResponse>(
    "/contact",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function getModerationComments(token: string, moderationStatus?: string | null): Promise<ModerationComment[]> {
  const suffix = moderationStatus ? `?moderation_status=${encodeURIComponent(moderationStatus)}` : "";
  return request<ModerationComment[]>(`/parent/content/comments${suffix}`, {}, token);
}

export function moderateComment(
  commentId: number,
  payload: { moderation_status: "approved" | "rejected"; moderation_notes?: string | null },
  token: string,
): Promise<{ status: string; comment_id: number }> {
  return request<{ status: string; comment_id: number }>(
    `/parent/content/comments/${commentId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function getContactSubmissions(token: string, deliveryStatus?: string | null): Promise<ContactSubmissionRecord[]> {
  const suffix = deliveryStatus ? `?delivery_status=${encodeURIComponent(deliveryStatus)}` : "";
  return request<ContactSubmissionRecord[]>(`/parent/content/contact-submissions${suffix}`, {}, token);
}
