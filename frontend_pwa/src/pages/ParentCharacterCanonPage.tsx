import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  enhanceCharacterCanonPreview,
  getCharacterCanonDetail,
  getCharacterCanonOverview,
  publishCharacterCanon,
  saveCharacterCanon,
  type CharacterCanonDetailResponse,
  type CharacterCanonOverviewResponse,
  type CharacterCanonPreviewResponse,
} from "../services/api";
import { useAuth } from "../services/auth";

function asStringList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  return [];
}

function asText(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return null;
}

export function ParentCharacterCanonPage() {
  const { readerId, worldId } = useParams();
  const { token } = useAuth();
  const [overview, setOverview] = useState<CharacterCanonOverviewResponse | null>(null);
  const [detail, setDetail] = useState<CharacterCanonDetailResponse | null>(null);
  const [selectedCharacterId, setSelectedCharacterId] = useState<number | null>(null);
  const [preview, setPreview] = useState<CharacterCanonPreviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [isLocked, setIsLocked] = useState(false);
  const [isMajorCharacter, setIsMajorCharacter] = useState(false);

  async function loadOverview(activeToken: string, activeReaderId: number, activeWorldId: number) {
    const payload = await getCharacterCanonOverview(activeReaderId, activeWorldId, activeToken);
    setOverview(payload);
    const nextCharacterId =
      selectedCharacterId && payload.characters.some((item) => item.character_id === selectedCharacterId)
        ? selectedCharacterId
        : payload.characters[0]?.character_id ?? null;
    setSelectedCharacterId(nextCharacterId);
    return nextCharacterId;
  }

  async function loadDetail(activeToken: string, activeReaderId: number, activeWorldId: number, characterId: number) {
    setDetailLoading(true);
    try {
      const payload = await getCharacterCanonDetail(activeReaderId, activeWorldId, characterId, activeToken);
      setDetail(payload);
      setPreview(null);
      setNotes(asText(payload.canon.notes) ?? "");
      setIsLocked(Boolean(payload.canon.is_locked));
      setIsMajorCharacter(Boolean(payload.canon.is_major_character));
    } finally {
      setDetailLoading(false);
    }
  }

  useEffect(() => {
    if (!token || !readerId || !worldId) {
      return;
    }

    setLoading(true);
    setError(null);
    loadOverview(token, Number(readerId), Number(worldId))
      .then((firstCharacterId) => {
        if (firstCharacterId) {
          return loadDetail(token, Number(readerId), Number(worldId), firstCharacterId);
        }
        setDetail(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to open character canon."))
      .finally(() => setLoading(false));
  }, [readerId, token, worldId]);

  useEffect(() => {
    if (!token || !readerId || !worldId || !selectedCharacterId || !overview) {
      return;
    }
    if (detail?.character.character_id === selectedCharacterId) {
      return;
    }
    loadDetail(token, Number(readerId), Number(worldId), selectedCharacterId).catch((err) =>
      setError(err instanceof Error ? err.message : "Unable to load the selected character."),
    );
  }, [detail?.character.character_id, overview, readerId, selectedCharacterId, token, worldId]);

  async function refreshAll(activeCharacterId?: number | null) {
    if (!token || !readerId || !worldId) {
      return;
    }
    const nextCharacterId = await loadOverview(token, Number(readerId), Number(worldId));
    const resolvedCharacterId = activeCharacterId ?? nextCharacterId;
    if (resolvedCharacterId) {
      await loadDetail(token, Number(readerId), Number(worldId), resolvedCharacterId);
    }
  }

  async function handleEnhance(sectionMode: "full" | "narrative" | "visual") {
    if (!token || !readerId || !worldId || !selectedCharacterId) {
      return;
    }
    setWorking(sectionMode);
    setNotice(null);
    setError(null);
    try {
      const payload = await enhanceCharacterCanonPreview(
        Number(readerId),
        Number(worldId),
        selectedCharacterId,
        { section_mode: sectionMode },
        token,
      );
      setPreview(payload);
      setNotes(asText(payload.preview_profile.notes) ?? notes);
      setIsLocked(Boolean(payload.preview_profile.is_locked));
      setIsMajorCharacter(Boolean(payload.preview_profile.is_major_character));
      setNotice(`Preview ready for ${sectionMode === "full" ? "full canon" : `${sectionMode} canon`}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to enhance character canon.");
    } finally {
      setWorking(null);
    }
  }

  function buildSavePayload(): { updates: Record<string, unknown>; enhancement_run_id?: number | null } {
    const base = preview?.preview_profile ? { ...preview.preview_profile } : {};
    return {
      updates: {
        ...base,
        notes,
        is_locked: isLocked,
        is_major_character: isMajorCharacter,
      },
      enhancement_run_id:
        typeof preview?.enhancement_run?.enhancement_run_id === "number"
          ? (preview.enhancement_run.enhancement_run_id as number)
          : null,
    };
  }

  async function handleSave(publish: boolean) {
    if (!token || !readerId || !worldId || !selectedCharacterId) {
      return;
    }
    setWorking(publish ? "publish" : "save");
    setNotice(null);
    setError(null);
    try {
      const payload = buildSavePayload();
      if (publish) {
        await publishCharacterCanon(Number(readerId), Number(worldId), selectedCharacterId, payload, token);
      } else {
        await saveCharacterCanon(Number(readerId), Number(worldId), selectedCharacterId, payload, token);
      }
      await refreshAll(selectedCharacterId);
      setNotice(publish ? "Canonical profile published." : "Character canon saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save character canon.");
    } finally {
      setWorking(null);
    }
  }

  if (loading) {
    return <LoadingState label="Opening character canon studio..." />;
  }

  if (error && !overview) {
    return <ErrorState message={error} />;
  }

  if (!overview) {
    return <ErrorState message="Character canon overview unavailable." />;
  }

  const activeCanon = preview?.preview_profile ?? detail?.canon ?? {};
  const narrativeTraits = asStringList(activeCanon.dominant_traits);
  const motivations = asStringList(activeCanon.core_motivations);
  const anchors = asStringList(activeCanon.continuity_anchors);
  const visualLocks = asStringList(activeCanon.visual_must_never_change);
  const signatureFeatures = asStringList(activeCanon.signature_physical_features);

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Character canon</p>
            <h1>{overview.world.name ?? "Reader world"} canon studio</h1>
            <p>
              Review existing residents, enhance them into structured canon, and publish stable persona and visual
              rules back into the live platform.
            </p>
          </div>
          <div className="library-action-row">
            <Link to={`/parent/readers/${readerId}`} className="ghost-button">
              Reader workspace
            </Link>
            <Link to={`/reader/${readerId}/worlds/${worldId}`} className="ghost-button">
              World info
            </Link>
          </div>
        </div>

        {notice ? (
          <div className="status-card dashboard-notice-card">
            <h3>Saved</h3>
            <p>{notice}</p>
          </div>
        ) : null}

        {error ? (
          <div className="status-card">
            <h3>Something needs attention</h3>
            <p>{error}</p>
          </div>
        ) : null}
      </section>

      <section className="panel canon-layout">
        <aside className="panel inset-panel canon-sidebar">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Characters</p>
              <h2>Canon coverage</h2>
            </div>
          </div>
          <div className="canon-character-list">
            {overview.characters.map((character) => (
              <button
                key={character.character_id}
                type="button"
                className={`canon-character-button ${selectedCharacterId === character.character_id ? "is-active" : ""}`}
                onClick={() => setSelectedCharacterId(character.character_id)}
              >
                <strong>{character.name ?? `Character ${character.character_id}`}</strong>
                <span>{character.species ?? "Unknown type"}</span>
                <small>
                  {character.canon_status} {character.canon_version ? `· v${character.canon_version}` : ""}
                </small>
              </button>
            ))}
          </div>
        </aside>

        <div className="canon-main">
          {detailLoading ? <LoadingState label="Loading character canon..." /> : null}

          {detail ? (
            <>
              <section className="panel inset-panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Current character</p>
                    <h2>{detail.character.name ?? `Character ${detail.character.character_id}`}</h2>
                    <p>
                      {detail.character.species ?? "Unknown type"} · source status{" "}
                      {String(activeCanon.source_status ?? "legacy")}
                    </p>
                  </div>
                  <div className="library-action-row">
                    <button
                      type="button"
                      className="ghost-button"
                      disabled={working !== null}
                      onClick={() => handleEnhance("narrative")}
                    >
                      {working === "narrative" ? "Enhancing..." : "Enhance narrative"}
                    </button>
                    <button
                      type="button"
                      className="ghost-button"
                      disabled={working !== null}
                      onClick={() => handleEnhance("visual")}
                    >
                      {working === "visual" ? "Enhancing..." : "Enhance visual"}
                    </button>
                    <button
                      type="button"
                      className="primary-button"
                      disabled={working !== null}
                      onClick={() => handleEnhance("full")}
                    >
                      {working === "full" ? "Enhancing..." : "Enhance full canon"}
                    </button>
                  </div>
                </div>

                <div className="dashboard-summary-grid">
                  <article className="status-card dashboard-summary-card">
                    <p className="eyebrow">Essence</p>
                    <h3>{asText(activeCanon.one_sentence_essence) ?? "Not defined yet"}</h3>
                    <p>{asText(activeCanon.role_in_world) ?? "Role not locked yet"}</p>
                  </article>
                  <article className="status-card dashboard-summary-card">
                    <p className="eyebrow">Voice</p>
                    <h3>{asText(activeCanon.speech_style) ?? "No speech style yet"}</h3>
                    <p>{asText(activeCanon.relationship_tendencies) ?? "Relationship tendencies pending"}</p>
                  </article>
                  <article className="status-card dashboard-summary-card">
                    <p className="eyebrow">Visual identity</p>
                    <h3>{asText(activeCanon.visual_summary) ?? "No visual canon yet"}</h3>
                    <p>{asText(activeCanon.art_style_constraints) ?? "Art constraints not locked yet"}</p>
                  </article>
                  <article className="status-card dashboard-summary-card">
                    <p className="eyebrow">Metadata</p>
                    <h3>Version {String(activeCanon.canon_version ?? "0")}</h3>
                    <p>{Boolean(activeCanon.is_locked) ? "Locked" : "Editable"} · {Boolean(activeCanon.is_major_character) ? "Major character" : "Supporting character"}</p>
                  </article>
                </div>
              </section>

              <section className="panel inset-panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Narrative persona</p>
                    <h2>Behavior, motivation, and voice</h2>
                  </div>
                </div>
                <div className="parent-detail-grid">
                  <article className="panel inset-panel">
                    <p className="eyebrow">Summary</p>
                    <p>{asText(activeCanon.full_personality_summary) ?? "No personality summary yet."}</p>
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Dominant traits</p>
                    <p>{narrativeTraits.length > 0 ? narrativeTraits.join(", ") : "No dominant traits locked yet."}</p>
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Motivations</p>
                    <p>{motivations.length > 0 ? motivations.join(", ") : "No core motivations locked yet."}</p>
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Continuity anchors</p>
                    <p>{anchors.length > 0 ? anchors.join(", ") : "No continuity anchors locked yet."}</p>
                  </article>
                </div>
              </section>

              <section className="panel inset-panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Visual identity</p>
                    <h2>Illustration consistency guidance</h2>
                  </div>
                </div>
                <div className="parent-detail-grid">
                  <article className="panel inset-panel">
                    <p className="eyebrow">Signature features</p>
                    <p>{signatureFeatures.length > 0 ? signatureFeatures.join(", ") : "No signature features yet."}</p>
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Must never change</p>
                    <p>{visualLocks.length > 0 ? visualLocks.join(", ") : "No hard visual locks yet."}</p>
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Color palette</p>
                    <p>{asStringList(activeCanon.color_palette).join(", ") || "No palette defined yet."}</p>
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Clothing and accessories</p>
                    <p>{asText(activeCanon.clothing_and_accessories) ?? "No signature clothing/accessories yet."}</p>
                  </article>
                </div>
              </section>

              <section className="panel inset-panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Prompt packs and controls</p>
                    <h2>Runtime canon payloads</h2>
                  </div>
                </div>

                <div className="world-management-grid">
                  <article className="panel inset-panel">
                    <p className="eyebrow">Narrative prompt pack</p>
                    <p>{asText(activeCanon.narrative_prompt_pack_short) ?? "Not generated yet."}</p>
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Visual prompt pack</p>
                    <p>{asText(activeCanon.visual_prompt_pack_short) ?? "Not generated yet."}</p>
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Continuity lock pack</p>
                    <p>{asText(activeCanon.continuity_lock_pack) ?? "Not generated yet."}</p>
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Review controls</p>
                    <label className="field">
                      <span>Notes</span>
                      <textarea
                        className="tooling-textarea"
                        value={notes}
                        onChange={(event) => setNotes(event.target.value)}
                        placeholder="Add editorial notes or approval guidance."
                      />
                    </label>
                    <label className="checkbox-field">
                      <input type="checkbox" checked={isMajorCharacter} onChange={(event) => setIsMajorCharacter(event.target.checked)} />
                      <span>Major recurring character</span>
                    </label>
                    <label className="checkbox-field">
                      <input type="checkbox" checked={isLocked} onChange={(event) => setIsLocked(event.target.checked)} />
                      <span>Lock canon after review</span>
                    </label>
                    <div className="library-action-row">
                      <button type="button" className="ghost-button" disabled={working !== null} onClick={() => handleSave(false)}>
                        {working === "save" ? "Saving..." : "Save draft canon"}
                      </button>
                      <button type="button" className="primary-button" disabled={working !== null} onClick={() => handleSave(true)}>
                        {working === "publish" ? "Publishing..." : "Publish canon"}
                      </button>
                    </div>
                  </article>
                </div>
              </section>

              <section className="panel inset-panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Context and audit</p>
                    <h2>World context, relationships, and versioning</h2>
                  </div>
                </div>
                <div className="world-management-grid">
                  <article className="panel inset-panel">
                    <p className="eyebrow">Relationships</p>
                    {detail.relationships.length > 0 ? (
                      <ul className="tooling-conflict-list">
                        {detail.relationships.map((relationship, index) => (
                          <li key={`${relationship.relationship_id ?? index}`}>
                            {String(relationship.relationship_type ?? "Relationship")} · strength{" "}
                            {String(relationship.relationship_strength ?? "?")}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>No related relationships found yet.</p>
                    )}
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Recent memory</p>
                    {detail.recent_memory_events.length > 0 ? (
                      <ul className="tooling-conflict-list">
                        {detail.recent_memory_events.map((event, index) => (
                          <li key={`${event.event_id ?? index}`}>{String(event.event_summary ?? "Stored memory event")}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>No recent memory events for this character yet.</p>
                    )}
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">World rules</p>
                    {detail.world_rules.length > 0 ? (
                      <ul className="tooling-conflict-list">
                        {detail.world_rules.slice(0, 5).map((rule, index) => (
                          <li key={`${rule.rule_id ?? index}`}>{String(rule.rule_description ?? rule.rule_type ?? "World rule")}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>No world rules available.</p>
                    )}
                  </article>
                  <article className="panel inset-panel">
                    <p className="eyebrow">Version history</p>
                    {detail.history.length > 0 ? (
                      <ul className="tooling-conflict-list">
                        {detail.history.map((item, index) => (
                          <li key={`${item.version_id ?? index}`}>
                            v{String(item.canon_version ?? "?")} · {String(item.source_status ?? "draft")}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>No prior canon versions yet.</p>
                    )}
                  </article>
                </div>
              </section>
            </>
          ) : (
            <div className="status-card">
              <h3>No characters available</h3>
              <p>Add characters to this reader world before building canon.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
