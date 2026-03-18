import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  checkReaderWorldCharacterContinuity,
  checkReaderWorldContinuity,
  createReaderWorldCharacter,
  createReaderWorldLocation,
  createReaderWorldRelationship,
  getReaderWorldCharacterHistory,
  getReaderWorldHistory,
  getWorldDetails,
  type Character,
  type ContinuityResponse,
  type StoryMemoryEvent,
  type WorldDetailsResponse,
} from "../services/api";
import { useAuth } from "../services/auth";

function normalizeTraits(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  }
  if (typeof value === "string" && value.trim()) {
    try {
      const parsed = JSON.parse(value) as unknown;
      if (Array.isArray(parsed)) {
        return parsed.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
      }
    } catch {
      return [value.trim()];
    }
    return [value.trim()];
  }
  return [];
}

function renderCharacterSubtitle(character: Character): string {
  const traits = normalizeTraits(character.personality_traits);
  const parts = [character.species, traits.length > 0 ? traits.join(", ") : null].filter(Boolean);
  return parts.join(" | ");
}

function splitTraits(raw: string): string[] {
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function WorldInfoPage() {
  const { readerId, worldId } = useParams();
  const { token } = useAuth();
  const [details, setDetails] = useState<WorldDetailsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [toolError, setToolError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [savingLocation, setSavingLocation] = useState(false);
  const [savingCharacter, setSavingCharacter] = useState(false);
  const [savingRelationship, setSavingRelationship] = useState(false);
  const [loadingWorldHistory, setLoadingWorldHistory] = useState(false);
  const [loadingCharacterHistoryId, setLoadingCharacterHistoryId] = useState<number | null>(null);
  const [checkingWorldContinuity, setCheckingWorldContinuity] = useState(false);
  const [checkingCharacterContinuityId, setCheckingCharacterContinuityId] = useState<number | null>(null);
  const [locationName, setLocationName] = useState("");
  const [locationDescription, setLocationDescription] = useState("");
  const [characterName, setCharacterName] = useState("");
  const [characterSpecies, setCharacterSpecies] = useState("");
  const [characterTraits, setCharacterTraits] = useState("");
  const [characterHomeLocation, setCharacterHomeLocation] = useState<number | "">("");
  const [relationshipCharacterA, setRelationshipCharacterA] = useState<number | "">("");
  const [relationshipCharacterB, setRelationshipCharacterB] = useState<number | "">("");
  const [relationshipType, setRelationshipType] = useState("");
  const [relationshipStrength, setRelationshipStrength] = useState(5);
  const [worldHistory, setWorldHistory] = useState<StoryMemoryEvent[] | null>(null);
  const [characterHistories, setCharacterHistories] = useState<Record<number, StoryMemoryEvent[]>>({});
  const [worldContinuitySummary, setWorldContinuitySummary] = useState("");
  const [worldContinuity, setWorldContinuity] = useState<ContinuityResponse | null>(null);
  const [characterContinuitySummary, setCharacterContinuitySummary] = useState<Record<number, string>>({});
  const [characterContinuity, setCharacterContinuity] = useState<Record<number, ContinuityResponse>>({});

  async function loadWorld(activeToken: string, activeReaderId: number, activeWorldId: number) {
    const payload = await getWorldDetails(activeReaderId, activeWorldId, activeToken);
    setDetails(payload);
  }

  useEffect(() => {
    if (!token || !worldId || !readerId) {
      return;
    }

    loadWorld(token, Number(readerId), Number(worldId))
      .catch((err) => setPageError(err instanceof Error ? err.message : "Unable to load world details."))
      .finally(() => setLoading(false));
  }, [readerId, token, worldId]);

  const locationMap = useMemo(() => {
    const map = new Map<number, string>();
    for (const location of details?.locations ?? []) {
      if (typeof location.location_id === "number" && location.name) {
        map.set(location.location_id, location.name);
      }
    }
    return map;
  }, [details?.locations]);

  const characterMap = useMemo(() => {
    const map = new Map<number, string>();
    for (const character of details?.characters ?? []) {
      if (typeof character.character_id === "number" && character.name) {
        map.set(character.character_id, character.name);
      }
    }
    return map;
  }, [details?.characters]);

  async function refreshWorld() {
    if (!token || !readerId || !worldId) {
      return;
    }
    await loadWorld(token, Number(readerId), Number(worldId));
  }

  async function handleCreateLocation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !readerId || !worldId) {
      return;
    }

    setSavingLocation(true);
    setToolError(null);
    setNotice(null);

    try {
      await createReaderWorldLocation(
        Number(readerId),
        Number(worldId),
        {
          name: locationName.trim(),
          description: locationDescription.trim() || null,
        },
        token,
      );
      await refreshWorld();
      setLocationName("");
      setLocationDescription("");
      setNotice("Location added to this reader world.");
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to create location.");
    } finally {
      setSavingLocation(false);
    }
  }

  async function handleCreateCharacter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !readerId || !worldId) {
      return;
    }

    setSavingCharacter(true);
    setToolError(null);
    setNotice(null);

    try {
      await createReaderWorldCharacter(
        Number(readerId),
        Number(worldId),
        {
          name: characterName.trim(),
          species: characterSpecies.trim(),
          personality_traits: JSON.stringify(splitTraits(characterTraits)),
          home_location: characterHomeLocation === "" ? null : characterHomeLocation,
        },
        token,
      );
      await refreshWorld();
      setCharacterName("");
      setCharacterSpecies("");
      setCharacterTraits("");
      setCharacterHomeLocation("");
      setNotice("Character added to this reader world.");
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to create character.");
    } finally {
      setSavingCharacter(false);
    }
  }

  async function handleCreateRelationship(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !readerId || !worldId || relationshipCharacterA === "" || relationshipCharacterB === "") {
      return;
    }

    setSavingRelationship(true);
    setToolError(null);
    setNotice(null);

    try {
      await createReaderWorldRelationship(
        Number(readerId),
        Number(worldId),
        {
          character_a: relationshipCharacterA,
          character_b: relationshipCharacterB,
          relationship_type: relationshipType.trim(),
          relationship_strength: relationshipStrength,
        },
        token,
      );
      await refreshWorld();
      setRelationshipCharacterA("");
      setRelationshipCharacterB("");
      setRelationshipType("");
      setRelationshipStrength(5);
      setNotice("Relationship added to this reader world.");
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to create relationship.");
    } finally {
      setSavingRelationship(false);
    }
  }

  async function handleLoadWorldHistory() {
    if (!token || !readerId || !worldId) {
      return;
    }

    setLoadingWorldHistory(true);
    setToolError(null);
    try {
      const payload = await getReaderWorldHistory(Number(readerId), Number(worldId), token);
      setWorldHistory(payload);
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to load world history.");
    } finally {
      setLoadingWorldHistory(false);
    }
  }

  async function handleLoadCharacterHistory(characterId: number) {
    if (!token || !readerId || !worldId) {
      return;
    }
    setLoadingCharacterHistoryId(characterId);
    setToolError(null);
    try {
      const payload = await getReaderWorldCharacterHistory(Number(readerId), Number(worldId), characterId, token);
      setCharacterHistories((current) => ({ ...current, [characterId]: payload }));
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to load character history.");
    } finally {
      setLoadingCharacterHistoryId(null);
    }
  }

  async function handleCheckWorldContinuity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !readerId || !worldId || !worldContinuitySummary.trim()) {
      return;
    }

    setCheckingWorldContinuity(true);
    setToolError(null);
    try {
      const payload = await checkReaderWorldContinuity(Number(readerId), Number(worldId), worldContinuitySummary.trim(), token);
      setWorldContinuity(payload);
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to run world continuity check.");
    } finally {
      setCheckingWorldContinuity(false);
    }
  }

  async function handleCheckCharacterContinuity(event: FormEvent<HTMLFormElement>, characterId: number) {
    event.preventDefault();
    if (!token || !readerId || !worldId || !characterContinuitySummary[characterId]?.trim()) {
      return;
    }

    setCheckingCharacterContinuityId(characterId);
    setToolError(null);
    try {
      const payload = await checkReaderWorldCharacterContinuity(
        Number(readerId),
        Number(worldId),
        characterId,
        characterContinuitySummary[characterId].trim(),
        token,
      );
      setCharacterContinuity((current) => ({ ...current, [characterId]: payload }));
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to run character continuity check.");
    } finally {
      setCheckingCharacterContinuityId(null);
    }
  }

  if (loading) {
    return <LoadingState label="Opening world details..." />;
  }

  if (pageError) {
    return <ErrorState message={pageError} />;
  }

  if (!details) {
    return <ErrorState message="World details are unavailable." />;
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">World information</p>
          <h1>{details.world.name ?? `World ${details.world.world_id}`}</h1>
          <p>{details.world.description ?? "No world description is available yet."}</p>
        </div>
        <div className="library-action-row">
          <Link to={`/reader/${readerId}/books`} className="ghost-button">
            Back to books
          </Link>
          <Link to={`/reader/${readerId}/games`} className="ghost-button">
            Open game shelf
          </Link>
        </div>
      </div>

      {notice ? (
        <div className="status-card dashboard-notice-card">
          <h3>Saved</h3>
          <p>{notice}</p>
        </div>
      ) : null}

      {toolError ? (
        <div className="status-card">
          <h3>Tooling issue</h3>
          <p>{toolError}</p>
        </div>
      ) : null}

      <div className="detail-grid">
        <article className="panel inset-panel">
          <p className="eyebrow">Locations</p>
          <h3>{details.locations.length}</h3>
          <p>Places readers can visit in this world.</p>
        </article>
        <article className="panel inset-panel">
          <p className="eyebrow">Characters</p>
          <h3>{details.characters.length}</h3>
          <p>Story companions, guides, and world residents.</p>
        </article>
        <article className="panel inset-panel">
          <p className="eyebrow">World rules</p>
          <h3>{details.world_rules.length}</h3>
          <p>Rules and story logic that shape this universe.</p>
        </article>
        <article className="panel inset-panel">
          <p className="eyebrow">Editing scope</p>
          <h3>Reader-owned additions</h3>
          <p>New items from this page are added to the reader's custom world layer without overwriting the shared template.</p>
        </article>
      </div>

      <section className="panel inset-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Overview</p>
            <h2>World description</h2>
          </div>
        </div>
        <p>{details.world.description ?? "No long-form description is available for this world yet."}</p>
      </section>

      <div className="world-management-grid">
        <section className="panel inset-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Add location</p>
              <h2>Create a new place</h2>
            </div>
          </div>
          <form className="world-assignment-form" onSubmit={handleCreateLocation}>
            <label className="field">
              <span>Location name</span>
              <input value={locationName} onChange={(event) => setLocationName(event.target.value)} required />
            </label>
            <label className="field">
              <span>Description</span>
              <input
                value={locationDescription}
                onChange={(event) => setLocationDescription(event.target.value)}
                placeholder="Describe the place"
              />
            </label>
            <button type="submit" className="primary-button" disabled={savingLocation || !locationName.trim()}>
              {savingLocation ? "Adding location..." : "Add location"}
            </button>
          </form>
        </section>

        <section className="panel inset-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Add character</p>
              <h2>Create a new resident</h2>
            </div>
          </div>
          <form className="world-assignment-form" onSubmit={handleCreateCharacter}>
            <label className="field">
              <span>Character name</span>
              <input value={characterName} onChange={(event) => setCharacterName(event.target.value)} required />
            </label>
            <label className="field">
              <span>Species</span>
              <input value={characterSpecies} onChange={(event) => setCharacterSpecies(event.target.value)} required />
            </label>
            <label className="field">
              <span>Traits</span>
              <input
                value={characterTraits}
                onChange={(event) => setCharacterTraits(event.target.value)}
                placeholder="brave, curious, gentle"
                required
              />
            </label>
            <label className="field">
              <span>Home location</span>
              <select
                value={characterHomeLocation}
                onChange={(event) => setCharacterHomeLocation(event.target.value ? Number(event.target.value) : "")}
              >
                <option value="">No home location</option>
                {details.locations.map((location) => (
                  <option key={location.location_id} value={location.location_id}>
                    {location.name ?? `Location ${location.location_id}`}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="submit"
              className="primary-button"
              disabled={savingCharacter || !characterName.trim() || !characterSpecies.trim() || splitTraits(characterTraits).length === 0}
            >
              {savingCharacter ? "Adding character..." : "Add character"}
            </button>
          </form>
        </section>

        <section className="panel inset-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Add relationship</p>
              <h2>Connect two characters</h2>
            </div>
          </div>
          <form className="world-assignment-form" onSubmit={handleCreateRelationship}>
            <label className="field">
              <span>Character A</span>
              <select
                value={relationshipCharacterA}
                onChange={(event) => setRelationshipCharacterA(event.target.value ? Number(event.target.value) : "")}
                required
              >
                <option value="">Choose a character</option>
                {details.characters.map((character) => (
                  <option key={character.character_id} value={character.character_id}>
                    {character.name ?? `Character ${character.character_id}`}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Character B</span>
              <select
                value={relationshipCharacterB}
                onChange={(event) => setRelationshipCharacterB(event.target.value ? Number(event.target.value) : "")}
                required
              >
                <option value="">Choose a character</option>
                {details.characters.map((character) => (
                  <option key={character.character_id} value={character.character_id}>
                    {character.name ?? `Character ${character.character_id}`}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Relationship type</span>
              <input
                value={relationshipType}
                onChange={(event) => setRelationshipType(event.target.value)}
                placeholder="friends, rivals, mentor"
                required
              />
            </label>
            <label className="field">
              <span>Strength</span>
              <select value={relationshipStrength} onChange={(event) => setRelationshipStrength(Number(event.target.value))}>
                {Array.from({ length: 11 }, (_, index) => (
                  <option key={index} value={index}>
                    {index}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="submit"
              className="primary-button"
              disabled={
                savingRelationship ||
                relationshipCharacterA === "" ||
                relationshipCharacterB === "" ||
                relationshipCharacterA === relationshipCharacterB ||
                !relationshipType.trim()
              }
            >
              {savingRelationship ? "Adding relationship..." : "Add relationship"}
            </button>
          </form>
        </section>
      </div>

      <div className="tooling-grid">
        <section className="panel inset-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Memory</p>
              <h2>World history</h2>
              <p>Inspect stored events associated with this world.</p>
            </div>
            <button type="button" className="ghost-button" onClick={handleLoadWorldHistory} disabled={loadingWorldHistory}>
              {loadingWorldHistory ? "Loading history..." : "Load world history"}
            </button>
          </div>
          <div className="tooling-list">
            {worldHistory ? (
              worldHistory.length > 0 ? (
                worldHistory.map((event) => (
                  <article key={event.event_id} className="panel inset-panel tooling-card">
                    <h3>Event {event.event_id}</h3>
                    <p>{event.event_summary ?? "No summary available."}</p>
                    {event.location_id ? <p>Location ID: {event.location_id}</p> : null}
                    {event.characters?.length ? <p>Characters: {event.characters.join(", ")}</p> : null}
                  </article>
                ))
              ) : (
                <div className="status-card">
                  <h3>No world history yet</h3>
                  <p>No stored world events are currently available.</p>
                </div>
              )
            ) : (
              <div className="status-card">
                <h3>History not loaded</h3>
                <p>Use the button above to inspect world memory.</p>
              </div>
            )}
          </div>
        </section>

        <section className="panel inset-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Continuity</p>
              <h2>World continuity check</h2>
              <p>Validate a proposed story summary against the world's known rules, locations, and history.</p>
            </div>
          </div>
          <form className="world-assignment-form" onSubmit={handleCheckWorldContinuity}>
            <label className="field">
              <span>World summary or planned story</span>
              <textarea
                className="tooling-textarea"
                value={worldContinuitySummary}
                onChange={(event) => setWorldContinuitySummary(event.target.value)}
                placeholder="Describe a planned story or world change to check for conflicts."
              />
            </label>
            <button type="submit" className="primary-button" disabled={checkingWorldContinuity || !worldContinuitySummary.trim()}>
              {checkingWorldContinuity ? "Checking continuity..." : "Run world continuity check"}
            </button>
          </form>
          {worldContinuity ? (
            <div className="tooling-result-card">
              <h3>{worldContinuity.continuity_valid ? "Continuity valid" : "Continuity conflicts found"}</h3>
              {worldContinuity.conflicts.length > 0 ? (
                <ul className="tooling-conflict-list">
                  {worldContinuity.conflicts.map((conflict) => (
                    <li key={conflict}>{conflict}</li>
                  ))}
                </ul>
              ) : (
                <p>No continuity conflicts were detected.</p>
              )}
            </div>
          ) : null}
        </section>
      </div>

      <div className="library-shelf-grid">
        <section className="panel inset-panel world-shelf-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Locations</p>
              <h2>Places in this world</h2>
            </div>
          </div>
          <div className="library-grid">
            {details.locations.length > 0 ? (
              details.locations.map((location) => (
                <article key={location.location_id} className="panel inset-panel">
                  <h3>{location.name ?? `Location ${location.location_id}`}</h3>
                  <p>{location.description ?? "No description is available for this location yet."}</p>
                </article>
              ))
            ) : (
              <div className="status-card">
                <h3>No locations yet</h3>
                <p>This world does not have visible locations yet.</p>
              </div>
            )}
          </div>
        </section>

        <section className="panel inset-panel world-shelf-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Characters</p>
              <h2>Who lives here</h2>
            </div>
          </div>
          <div className="library-grid">
            {details.characters.length > 0 ? (
              details.characters.map((character) => (
                <article key={character.character_id} className="panel inset-panel">
                  <h3>{character.name ?? `Character ${character.character_id}`}</h3>
                  {renderCharacterSubtitle(character) ? <p>{renderCharacterSubtitle(character)}</p> : null}
                  {typeof character.home_location === "number" ? (
                    <p>Home: {locationMap.get(character.home_location) ?? `Location ${character.home_location}`}</p>
                  ) : null}

                  <div className="library-action-row">
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => handleLoadCharacterHistory(character.character_id)}
                      disabled={loadingCharacterHistoryId === character.character_id}
                    >
                      {loadingCharacterHistoryId === character.character_id ? "Loading history..." : "Character history"}
                    </button>
                  </div>

                  {characterHistories[character.character_id] ? (
                    <div className="tooling-mini-list">
                      {characterHistories[character.character_id].length > 0 ? (
                        characterHistories[character.character_id].map((event) => (
                          <div key={event.event_id} className="tooling-mini-card">
                            {event.event_summary ?? `Event ${event.event_id}`}
                          </div>
                        ))
                      ) : (
                        <div className="tooling-mini-card">No character history yet.</div>
                      )}
                    </div>
                  ) : null}

                  <form
                    className="world-assignment-form"
                    onSubmit={(event) => handleCheckCharacterContinuity(event, character.character_id)}
                  >
                    <label className="field">
                      <span>Character continuity summary</span>
                      <textarea
                        className="tooling-textarea"
                        value={characterContinuitySummary[character.character_id] ?? ""}
                        onChange={(event) =>
                          setCharacterContinuitySummary((current) => ({
                            ...current,
                            [character.character_id]: event.target.value,
                          }))
                        }
                        placeholder="Describe a planned character action or story beat to validate."
                      />
                    </label>
                    <button
                      type="submit"
                      className="primary-button"
                      disabled={
                        checkingCharacterContinuityId === character.character_id ||
                        !(characterContinuitySummary[character.character_id] ?? "").trim()
                      }
                    >
                      {checkingCharacterContinuityId === character.character_id ? "Checking..." : "Check character continuity"}
                    </button>
                  </form>

                  {characterContinuity[character.character_id] ? (
                    <div className="tooling-result-card">
                      <h3>
                        {characterContinuity[character.character_id].continuity_valid
                          ? "Continuity valid"
                          : "Continuity conflicts found"}
                      </h3>
                      {characterContinuity[character.character_id].conflicts.length > 0 ? (
                        <ul className="tooling-conflict-list">
                          {characterContinuity[character.character_id].conflicts.map((conflict) => (
                            <li key={conflict}>{conflict}</li>
                          ))}
                        </ul>
                      ) : (
                        <p>No continuity conflicts were detected.</p>
                      )}
                    </div>
                  ) : null}
                </article>
              ))
            ) : (
              <div className="status-card">
                <h3>No characters yet</h3>
                <p>This world does not have visible characters yet.</p>
              </div>
            )}
          </div>
        </section>
      </div>

      <section className="panel inset-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">World rules</p>
            <h2>Story logic and constraints</h2>
          </div>
        </div>
        <div className="library-grid">
          {details.world_rules.length > 0 ? (
            details.world_rules.map((rule) => (
              <article key={rule.rule_id} className="panel inset-panel">
                <h3>{rule.rule_type ?? `Rule ${rule.rule_id}`}</h3>
                <p>{rule.rule_description ?? "No rule description is available yet."}</p>
              </article>
            ))
          ) : (
            <div className="status-card">
              <h3>No world rules yet</h3>
              <p>This world does not have explicit rule entries yet.</p>
            </div>
          )}
        </div>
      </section>

      <section className="panel inset-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Character relationships</p>
            <h2>How characters connect</h2>
          </div>
        </div>
        <div className="library-grid">
          {details.relationships.length > 0 ? (
            details.relationships.map((relationship) => {
              const characterA =
                typeof relationship.character_a === "number"
                  ? characterMap.get(relationship.character_a) ?? `Character ${relationship.character_a}`
                  : "Unknown character";
              const characterB =
                typeof relationship.character_b === "number"
                  ? characterMap.get(relationship.character_b) ?? `Character ${relationship.character_b}`
                  : "Unknown character";

              return (
                <article key={relationship.relationship_id} className="panel inset-panel">
                  <h3>{relationship.relationship_type ?? `Relationship ${relationship.relationship_id}`}</h3>
                  <p>
                    {characterA} and {characterB}
                  </p>
                  {typeof relationship.relationship_strength === "number" ? (
                    <p>Strength: {relationship.relationship_strength}/10</p>
                  ) : null}
                </article>
              );
            })
          ) : (
            <div className="status-card">
              <h3>No relationships yet</h3>
              <p>This world does not have visible character relationships yet.</p>
            </div>
          )}
        </div>
      </section>
    </section>
  );
}
