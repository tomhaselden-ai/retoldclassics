import { FormEvent, useMemo, useState } from "react";

import type { Reader, ReaderInput } from "../services/api";

interface ReaderFormProps {
  initialReader?: Reader | null;
  onCancel?: () => void;
  onSubmit: (payload: ReaderInput) => Promise<void>;
  submitLabel: string;
  title: string;
}

function normalizeTraitFocus(value: unknown): string {
  if (Array.isArray(value)) {
    return value
      .map((item) => (typeof item === "string" ? item.trim() : ""))
      .filter(Boolean)
      .join(", ");
  }
  if (typeof value === "string") {
    return value;
  }
  return "";
}

export function ReaderForm({ initialReader, onCancel, onSubmit, submitLabel, title }: ReaderFormProps) {
  const defaults = useMemo(
    () => ({
      name: initialReader?.name ?? "",
      age: initialReader?.age ?? 7,
      readingLevel: initialReader?.reading_level ?? "",
      genderPreference: initialReader?.gender_preference ?? "",
      traitFocus: normalizeTraitFocus(initialReader?.trait_focus),
    }),
    [initialReader],
  );

  const [name, setName] = useState(defaults.name);
  const [age, setAge] = useState(defaults.age);
  const [readingLevel, setReadingLevel] = useState(defaults.readingLevel);
  const [genderPreference, setGenderPreference] = useState(defaults.genderPreference);
  const [traitFocus, setTraitFocus] = useState(defaults.traitFocus);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const parsedAge = Number(age);
    if (!Number.isFinite(parsedAge) || parsedAge < 0) {
      setError("Age must be zero or greater.");
      setSubmitting(false);
      return;
    }

    const payload: ReaderInput = {
      name: name.trim(),
      age: parsedAge,
      reading_level: readingLevel.trim(),
      gender_preference: genderPreference.trim(),
      trait_focus: traitFocus
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    };

    try {
      await onSubmit(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save the reader.");
      setSubmitting(false);
      return;
    }

    setSubmitting(false);
  }

  return (
    <form className="panel reader-form-panel" onSubmit={handleSubmit}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Reader profile</p>
          <h3>{title}</h3>
        </div>
      </div>

      <div className="reader-form-grid">
        <label className="field">
          <span>Name</span>
          <input value={name} onChange={(event) => setName(event.target.value)} required />
        </label>

        <label className="field">
          <span>Age</span>
          <input
            type="number"
            min={0}
            value={age}
            onChange={(event) => setAge(Number(event.target.value))}
            required
          />
        </label>

        <label className="field">
          <span>Reading level</span>
          <input value={readingLevel} onChange={(event) => setReadingLevel(event.target.value)} required />
        </label>

        <label className="field">
          <span>Gender preference</span>
          <input value={genderPreference} onChange={(event) => setGenderPreference(event.target.value)} required />
        </label>
      </div>

      <label className="field">
        <span>Trait focus</span>
        <input
          value={traitFocus}
          onChange={(event) => setTraitFocus(event.target.value)}
          placeholder="curiosity, courage, kindness"
        />
      </label>

      <p className="helper-text">Enter trait focus values as a comma-separated list.</p>

      {error ? (
        <div className="status-card error-card">
          <h3>Could not save reader</h3>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="reader-form-actions">
        <button type="submit" className="btn btn--admin btn-tone-mint primary-button" disabled={submitting}>
          {submitting ? "Saving..." : submitLabel}
        </button>
        {onCancel ? (
          <button type="button" className="btn btn--secondary btn-tone-neutral ghost-button" onClick={onCancel} disabled={submitting}>
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  );
}
