from sqlalchemy import inspect, text

from backend.db.database import engine


def ensure_reader_world_custom_world_schema() -> None:
    inspector = inspect(engine)

    account_columns = {column["name"] for column in inspector.get_columns("accounts")}
    world_columns = {column["name"] for column in inspector.get_columns("worlds")}
    reader_world_columns = {column["name"] for column in inspector.get_columns("reader_worlds")}

    with engine.begin() as connection:
        if "allowed_classics_authors" not in account_columns:
            connection.execute(text("ALTER TABLE accounts ADD COLUMN allowed_classics_authors JSON NULL"))

        if "parent_world_id" not in world_columns:
            connection.execute(text("ALTER TABLE worlds ADD COLUMN parent_world_id INT NULL"))
            connection.execute(text("CREATE INDEX idx_worlds_parent_world_id ON worlds (parent_world_id)"))

        if "derived_world_id" not in reader_world_columns:
            connection.execute(text("ALTER TABLE reader_worlds ADD COLUMN derived_world_id INT NULL"))
            connection.execute(
                text("CREATE INDEX idx_reader_worlds_derived_world_id ON reader_worlds (derived_world_id)")
            )


def ensure_media_job_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "media_jobs" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE media_jobs (
                        job_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        account_id INT NOT NULL,
                        story_id INT NOT NULL,
                        job_type VARCHAR(50) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        error_message TEXT NULL,
                        result_payload JSON NULL,
                        worker_id VARCHAR(100) NULL,
                        attempt_count INT NOT NULL DEFAULT 0,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        started_at TIMESTAMP NULL DEFAULT NULL,
                        completed_at TIMESTAMP NULL DEFAULT NULL,
                        CONSTRAINT fk_media_jobs_story FOREIGN KEY (story_id) REFERENCES stories_generated (story_id) ON DELETE CASCADE,
                        CONSTRAINT fk_media_jobs_account FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX idx_media_jobs_status_created ON media_jobs (status, created_at)"))
            connection.execute(text("CREATE INDEX idx_media_jobs_story_type_created ON media_jobs (story_id, job_type, created_at)"))


def ensure_guest_session_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "guest_sessions" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE guest_sessions (
                        session_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        session_token VARCHAR(96) NOT NULL,
                        last_ip VARCHAR(64) NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        last_seen_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NULL DEFAULT NULL,
                        CONSTRAINT uq_guest_sessions_token UNIQUE (session_token)
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX idx_guest_sessions_expires_at ON guest_sessions (expires_at)"))

        if "guest_usage_events" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE guest_usage_events (
                        event_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        session_id INT NOT NULL,
                        event_type VARCHAR(50) NOT NULL,
                        story_id INT NULL,
                        metadata_json JSON NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_guest_usage_events_session
                            FOREIGN KEY (session_id) REFERENCES guest_sessions (session_id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(
                text("CREATE INDEX idx_guest_usage_events_session_type ON guest_usage_events (session_id, event_type)")
            )
            connection.execute(
                text("CREATE INDEX idx_guest_usage_events_session_story_type ON guest_usage_events (session_id, story_id, event_type)")
            )


def ensure_parent_pin_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    account_columns = {column["name"] for column in inspector.get_columns("accounts")}

    with engine.begin() as connection:
        if "parent_pin_hash" not in account_columns:
            connection.execute(text("ALTER TABLE accounts ADD COLUMN parent_pin_hash VARCHAR(255) NULL"))
        if "parent_pin_enabled" not in account_columns:
            connection.execute(text("ALTER TABLE accounts ADD COLUMN parent_pin_enabled TINYINT(1) NOT NULL DEFAULT 0"))
        if "failed_pin_attempts" not in account_columns:
            connection.execute(text("ALTER TABLE accounts ADD COLUMN failed_pin_attempts INT NOT NULL DEFAULT 0"))
        if "parent_pin_locked_until" not in account_columns:
            connection.execute(text("ALTER TABLE accounts ADD COLUMN parent_pin_locked_until TIMESTAMP NULL DEFAULT NULL"))

        if "parent_pin_sessions" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE parent_pin_sessions (
                        session_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        account_id INT NOT NULL,
                        session_token VARCHAR(96) NOT NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NULL DEFAULT NULL,
                        revoked_at TIMESTAMP NULL DEFAULT NULL,
                        CONSTRAINT fk_parent_pin_sessions_account
                            FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE,
                        CONSTRAINT uq_parent_pin_sessions_token UNIQUE (session_token)
                    )
                    """
                )
            )
            connection.execute(
                text("CREATE INDEX idx_parent_pin_sessions_account_token ON parent_pin_sessions (account_id, session_token)")
            )


def ensure_goal_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "reader_goals" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE reader_goals (
                        goal_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        account_id INT NOT NULL,
                        reader_id INT NOT NULL,
                        goal_type VARCHAR(50) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        target_value INT NOT NULL,
                        is_active TINYINT(1) NOT NULL DEFAULT 1,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        CONSTRAINT fk_reader_goals_account FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE,
                        CONSTRAINT fk_reader_goals_reader FOREIGN KEY (reader_id) REFERENCES readers (reader_id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX idx_reader_goals_account_reader ON reader_goals (account_id, reader_id)"))

        if "reader_goal_progress" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE reader_goal_progress (
                        progress_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        goal_id INT NOT NULL,
                        reader_id INT NOT NULL,
                        current_value INT NOT NULL DEFAULT 0,
                        target_value INT NOT NULL,
                        progress_percent INT NOT NULL DEFAULT 0,
                        status VARCHAR(20) NOT NULL DEFAULT 'active',
                        updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP NULL DEFAULT NULL,
                        CONSTRAINT fk_reader_goal_progress_goal FOREIGN KEY (goal_id) REFERENCES reader_goals (goal_id) ON DELETE CASCADE,
                        CONSTRAINT fk_reader_goal_progress_reader FOREIGN KEY (reader_id) REFERENCES readers (reader_id) ON DELETE CASCADE,
                        CONSTRAINT uq_reader_goal_progress_goal UNIQUE (goal_id)
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX idx_reader_goal_progress_reader ON reader_goal_progress (reader_id, status)"))


def ensure_game_foundation_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    vocabulary_columns = {column["name"] for column in inspector.get_columns("vocabulary")}
    game_session_columns = {column["name"] for column in inspector.get_columns("game_sessions")} if "game_sessions" in table_names else set()

    with engine.begin() as connection:
        if "definition" not in vocabulary_columns:
            connection.execute(text("ALTER TABLE vocabulary ADD COLUMN definition TEXT NULL"))
        if "example_sentence" not in vocabulary_columns:
            connection.execute(text("ALTER TABLE vocabulary ADD COLUMN example_sentence TEXT NULL"))

        if "game_sessions" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE game_sessions (
                        session_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        account_id INT NOT NULL,
                        reader_id INT NOT NULL,
                        game_type VARCHAR(50) NOT NULL,
                        source_type VARCHAR(50) NOT NULL,
                        source_story_id INT NULL,
                        difficulty_level INT NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'ready',
                        item_count INT NOT NULL DEFAULT 0,
                        words_attempted INT NOT NULL DEFAULT 0,
                        words_correct INT NOT NULL DEFAULT 0,
                        words_incorrect INT NOT NULL DEFAULT 0,
                        hints_used INT NOT NULL DEFAULT 0,
                        completion_status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
                        started_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        ended_at TIMESTAMP NULL DEFAULT NULL,
                        duration_seconds INT NULL,
                        session_payload JSON NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        CONSTRAINT fk_game_sessions_account FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE,
                        CONSTRAINT fk_game_sessions_reader FOREIGN KEY (reader_id) REFERENCES readers (reader_id) ON DELETE CASCADE,
                        CONSTRAINT fk_game_sessions_story FOREIGN KEY (source_story_id) REFERENCES stories_generated (story_id) ON DELETE SET NULL
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX idx_game_sessions_reader_started ON game_sessions (reader_id, started_at)"))
            connection.execute(text("CREATE INDEX idx_game_sessions_reader_type_started ON game_sessions (reader_id, game_type, started_at)"))
        elif "session_payload" not in game_session_columns:
            connection.execute(text("ALTER TABLE game_sessions ADD COLUMN session_payload JSON NULL"))

        if "game_word_attempts" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE game_word_attempts (
                        attempt_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        session_id INT NOT NULL,
                        word_id INT NULL,
                        word_text VARCHAR(100) NOT NULL,
                        game_type VARCHAR(50) NOT NULL,
                        attempt_count INT NOT NULL DEFAULT 1,
                        correct TINYINT(1) NOT NULL DEFAULT 0,
                        time_spent_seconds INT NOT NULL DEFAULT 0,
                        hint_used TINYINT(1) NOT NULL DEFAULT 0,
                        skipped TINYINT(1) NOT NULL DEFAULT 0,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_game_word_attempts_session FOREIGN KEY (session_id) REFERENCES game_sessions (session_id) ON DELETE CASCADE,
                        CONSTRAINT fk_game_word_attempts_word FOREIGN KEY (word_id) REFERENCES vocabulary (word_id) ON DELETE SET NULL
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX idx_game_word_attempts_session ON game_word_attempts (session_id)"))
            connection.execute(text("CREATE INDEX idx_game_word_attempts_word ON game_word_attempts (word_id, game_type)"))


def ensure_character_canon_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "character_canon_profiles" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE character_canon_profiles (
                        canon_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        account_id INT NOT NULL,
                        character_id INT NOT NULL,
                        world_id INT NOT NULL,
                        reader_world_id INT NOT NULL,
                        name VARCHAR(255) NULL,
                        role_in_world VARCHAR(255) NULL,
                        species_or_type VARCHAR(100) NULL,
                        age_category VARCHAR(100) NULL,
                        gender_presentation VARCHAR(100) NULL,
                        archetype VARCHAR(255) NULL,
                        one_sentence_essence TEXT NULL,
                        full_personality_summary TEXT NULL,
                        dominant_traits JSON NULL,
                        secondary_traits JSON NULL,
                        core_motivations JSON NULL,
                        fears_and_vulnerabilities JSON NULL,
                        moral_tendencies JSON NULL,
                        behavioral_rules_usually JSON NULL,
                        behavioral_rules_never JSON NULL,
                        behavioral_rules_requires_justification JSON NULL,
                        speech_style TEXT NULL,
                        signature_expressions JSON NULL,
                        relationship_tendencies TEXT NULL,
                        growth_arc_pattern TEXT NULL,
                        continuity_anchors JSON NULL,
                        visual_summary TEXT NULL,
                        form_type VARCHAR(100) NULL,
                        anthropomorphic_level VARCHAR(100) NULL,
                        size_and_proportions TEXT NULL,
                        silhouette_description TEXT NULL,
                        facial_features TEXT NULL,
                        eye_description TEXT NULL,
                        fur_skin_surface_description TEXT NULL,
                        hair_feather_tail_details TEXT NULL,
                        clothing_and_accessories TEXT NULL,
                        signature_physical_features JSON NULL,
                        expression_range TEXT NULL,
                        movement_pose_tendencies TEXT NULL,
                        color_palette JSON NULL,
                        art_style_constraints TEXT NULL,
                        visual_must_never_change JSON NULL,
                        visual_may_change JSON NULL,
                        narrative_prompt_pack_short TEXT NULL,
                        visual_prompt_pack_short TEXT NULL,
                        continuity_lock_pack TEXT NULL,
                        source_status VARCHAR(20) NULL DEFAULT 'legacy',
                        canon_version INT NOT NULL DEFAULT 1,
                        enhanced_at TIMESTAMP NULL DEFAULT NULL,
                        enhanced_by INT NULL,
                        last_reviewed_at TIMESTAMP NULL DEFAULT NULL,
                        is_major_character TINYINT(1) NOT NULL DEFAULT 0,
                        is_locked TINYINT(1) NOT NULL DEFAULT 0,
                        notes TEXT NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        CONSTRAINT fk_character_canon_profiles_account FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE,
                        CONSTRAINT fk_character_canon_profiles_character FOREIGN KEY (character_id) REFERENCES characters (character_id) ON DELETE CASCADE,
                        CONSTRAINT fk_character_canon_profiles_reader_world FOREIGN KEY (reader_world_id) REFERENCES reader_worlds (reader_world_id) ON DELETE CASCADE,
                        CONSTRAINT uq_character_canon_profiles_scope UNIQUE (account_id, reader_world_id, character_id)
                    )
                    """
                )
            )
            connection.execute(
                text("CREATE INDEX idx_character_canon_profiles_world ON character_canon_profiles (reader_world_id, world_id)")
            )

        if "character_canon_versions" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE character_canon_versions (
                        version_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        canon_id INT NOT NULL,
                        account_id INT NOT NULL,
                        character_id INT NOT NULL,
                        reader_world_id INT NOT NULL,
                        canon_version INT NOT NULL,
                        source_status VARCHAR(20) NULL,
                        snapshot_json JSON NULL,
                        created_by INT NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_character_canon_versions_canon FOREIGN KEY (canon_id) REFERENCES character_canon_profiles (canon_id) ON DELETE CASCADE,
                        CONSTRAINT fk_character_canon_versions_account FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE,
                        CONSTRAINT fk_character_canon_versions_character FOREIGN KEY (character_id) REFERENCES characters (character_id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(
                text("CREATE INDEX idx_character_canon_versions_scope ON character_canon_versions (account_id, reader_world_id, character_id, canon_version)")
            )

        if "character_canon_enhancement_runs" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE character_canon_enhancement_runs (
                        enhancement_run_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        account_id INT NOT NULL,
                        character_id INT NOT NULL,
                        world_id INT NOT NULL,
                        reader_world_id INT NOT NULL,
                        section_mode VARCHAR(20) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        prompt_context_json JSON NULL,
                        generated_profile_json JSON NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        applied_at TIMESTAMP NULL DEFAULT NULL,
                        CONSTRAINT fk_character_canon_enhancement_runs_account FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE,
                        CONSTRAINT fk_character_canon_enhancement_runs_character FOREIGN KEY (character_id) REFERENCES characters (character_id) ON DELETE CASCADE,
                        CONSTRAINT fk_character_canon_enhancement_runs_reader_world FOREIGN KEY (reader_world_id) REFERENCES reader_worlds (reader_world_id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(
                text("CREATE INDEX idx_character_canon_enhancement_runs_scope ON character_canon_enhancement_runs (account_id, reader_world_id, character_id, enhancement_run_id)")
            )


def ensure_content_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "blog_posts" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE blog_posts (
                        post_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        slug VARCHAR(160) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        summary TEXT NOT NULL,
                        body_text LONGTEXT NOT NULL,
                        cover_eyebrow VARCHAR(120) NULL,
                        author_name VARCHAR(120) NOT NULL DEFAULT 'Retold Classics Studios',
                        status VARCHAR(20) NOT NULL DEFAULT 'published',
                        published_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        CONSTRAINT uq_blog_posts_slug UNIQUE (slug)
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX idx_blog_posts_status_published ON blog_posts (status, published_at)"))
            connection.execute(
                text(
                    """
                    INSERT INTO blog_posts (slug, title, summary, body_text, cover_eyebrow, author_name, status)
                    VALUES
                    (
                        'building-gentle-reading-routines-at-home',
                        'Building Gentle Reading Routines at Home',
                        'Small, repeatable reading moments can do more for confidence than long, high-pressure sessions.',
                        'A strong reading routine does not have to feel elaborate. For many families, the best rhythm starts with ten calm minutes, one familiar story, and a predictable place to begin.\n\nYoung readers build confidence when they know what comes next. A steady routine helps them settle in, notice patterns, and connect reading with comfort instead of pressure.\n\nThat is one reason we love a mix of classics, read-aloud support, and playful word practice. Families can revisit trusted stories, notice growth over time, and keep reading connected to everyday life.\n\nStoryBloom is built for that kind of rhythm: a welcoming shelf, child-friendly reading spaces, and family tools that support consistency without making reading time feel like school.',
                        'Reading routines',
                        'Retold Classics Studios',
                        'published'
                    ),
                    (
                        'why-classics-still-matter-for-early-readers',
                        'Why Classics Still Matter for Early Readers',
                        'Timeless stories give children strong language patterns, memorable characters, and stories worth returning to.',
                        'Classics endure for a reason. They offer strong story structure, memorable moral questions, and language that invites rereading.\n\nFor early readers, that matters. Familiar tales lower the barrier to entry while still leaving room for curiosity, discussion, and vocabulary growth.\n\nFamilies often tell us that children love revisiting a story once they feel ownership over it. A known tale becomes a place to practice expression, confidence, and comprehension.\n\nThat is the role classics play inside StoryBloom. They are not there as dusty artifacts. They are there as living story touchstones that children can read, hear, and return to as they grow.',
                        'Why classics',
                        'Retold Classics Studios',
                        'published'
                    )
                    """
                )
            )

        if "blog_comments" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE blog_comments (
                        comment_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        post_id INT NOT NULL,
                        author_name VARCHAR(80) NOT NULL,
                        author_email VARCHAR(255) NOT NULL,
                        comment_body TEXT NOT NULL,
                        moderation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        moderation_notes TEXT NULL,
                        moderated_by_email VARCHAR(255) NULL,
                        client_ip VARCHAR(64) NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        moderated_at TIMESTAMP NULL DEFAULT NULL,
                        CONSTRAINT fk_blog_comments_post FOREIGN KEY (post_id) REFERENCES blog_posts (post_id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(
                text("CREATE INDEX idx_blog_comments_post_status_created ON blog_comments (post_id, moderation_status, created_at)")
            )

        if "contact_submissions" not in table_names:
            connection.execute(
                text(
                    """
                    CREATE TABLE contact_submissions (
                        submission_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(120) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        subject VARCHAR(160) NOT NULL,
                        message TEXT NOT NULL,
                        delivery_status VARCHAR(20) NOT NULL DEFAULT 'queued',
                        client_ip VARCHAR(64) NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        delivered_at TIMESTAMP NULL DEFAULT NULL
                    )
                    """
                )
            )
            connection.execute(
                text("CREATE INDEX idx_contact_submissions_status_created ON contact_submissions (delivery_status, created_at)")
            )
