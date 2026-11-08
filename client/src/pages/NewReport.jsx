import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { categories, Message } from "../components/ReportUI";

const emptyReport = {
  title: "",
  description: "",
  location: "",
  category: "",
  priority: "Normal",
};

export default function NewReport() {
  const { user } = useAuth();
  const draftKey = `fixit-report-draft-${user.id}`;
  const [values, setValues] = useState(() => {
    try {
      const draft = JSON.parse(sessionStorage.getItem(draftKey));
      if (
        draft &&
        Object.keys(emptyReport).every((key) => typeof draft[key] === "string")
      )
        return { ...emptyReport, ...draft };
    } catch {
      /* The form also works when browser storage is unavailable. */
    }
    return { ...emptyReport, submission_key: crypto.randomUUID() };
  });
  const [error, setError] = useState(""),
    [errors, setErrors] = useState({}),
    [busy, setBusy] = useState(false);
  const [photo, setPhoto] = useState(null),
    [preview, setPreview] = useState(""),
    [photoError, setPhotoError] = useState("");
  const [created, setCreated] = useState(null);
  const fileInput = useRef(null),
    submitting = useRef(false);
  useEffect(() => {
    if (!created) {
      try {
        sessionStorage.setItem(draftKey, JSON.stringify(values));
      } catch {
        /* Draft storage is optional. */
      }
    }
  }, [values, draftKey, created]);
  useEffect(() => {
    if (!photo) {
      setPreview("");
      return;
    }
    const url = URL.createObjectURL(photo);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);
  const change = (event) =>
    setValues((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  function removePhoto() {
    setPhoto(null);
    setPhotoError("");
    setErrors((current) => ({ ...current, photo: "" }));
    if (fileInput.current) fileInput.current.value = "";
  }
  function selectPhoto(event) {
    const file = event.target.files[0];
    if (!file) return;
    setPhotoError("");
    setErrors((current) => ({ ...current, photo: "" }));
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setPhoto(null);
      event.target.value = "";
      setPhotoError("Only JPG, PNG, or WEBP images can be uploaded.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setPhoto(null);
      event.target.value = "";
      setPhotoError(
        "This photo is too large (maximum 5 MB). Please choose a smaller image.",
      );
      return;
    }
    setPhoto(file);
  }
  async function submit(event) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    setErrors({});
    const body = new FormData();
    Object.entries(values).forEach(([key, value]) => body.append(key, value));
    if (photo) body.append("photo", photo);
    try {
      const result = await api("/api/issues", { method: "POST", body });
      setCreated(result.issue);
      try {
        sessionStorage.removeItem(draftKey);
      } catch {
        /* Storage is optional. */
      }
      window.scrollTo(0, 0);
    } catch (problem) {
      setError(problem.message);
      setErrors(problem.errors || {});
      if (problem.status === 401) {
        try {
          sessionStorage.setItem(draftKey, JSON.stringify(values));
        } catch {
          /* Storage is optional. */
        }
      }
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  if (created)
    return (
      <section className="dashboard-page report-form-page">
        <div className="account-card report-confirmation" role="status">
          <span className="confirmation-mark" aria-hidden="true">
            ✓
          </span>
          <h1>Thank you!</h1>
          <p>
            Your report <strong>#{created.id}</strong> has been submitted.
          </p>
          <h2>{created.title}</h2>
          <p>
            {created.photo_url
              ? "Your photo was attached to the report."
              : "You submitted this report without a photo."}
          </p>
          <div className="hero-actions">
            <Link className="button primary" to={`/reports/${created.id}`}>
              View report
            </Link>
            <button
              className="button secondary"
              onClick={() => {
                setValues({
                  ...emptyReport,
                  submission_key: crypto.randomUUID(),
                });
                removePhoto();
                setCreated(null);
              }}
            >
              Report another problem
            </button>
          </div>
          <Link to="/my-reports">Back to My Reports</Link>
        </div>
      </section>
    );
  return (
    <section className="dashboard-page report-form-page">
      <Link to="/my-reports">← My Reports</Link>
      <h1>Report an issue</h1>
      <p className="muted">
        Tell us what happened and where. Description and photo are optional.
      </p>
      <p className="draft-note">
        Your report text stays in this tab. If your session ends, log in to
        continue. Reselect your photo afterward.
      </p>
      <Message>{error}</Message>
      <form className="account-card report-form" onSubmit={submit}>
        <fieldset disabled={busy}>
          {["title", "location"].map((name) => (
            <div className="form-field" key={name}>
              <label htmlFor={name}>
                {name === "title" ? "Issue title" : "Location"}
              </label>
              <input
                id={name}
                name={name}
                value={values[name]}
                onChange={change}
                required
                maxLength={name === "title" ? 100 : 200}
                placeholder={
                  name === "title"
                    ? "e.g. Broken light in the hallway"
                    : "e.g. Building A, second floor"
                }
                aria-invalid={!!errors[name]}
                aria-describedby={errors[name] ? `${name}-error` : undefined}
              />
              {name === "title" && <small>{values.title.length}/100</small>}
              {errors[name] && (
                <p className="field-error" id={`${name}-error`}>
                  {errors[name]}
                </p>
              )}
            </div>
          ))}
          <div className="form-field">
            <label htmlFor="description">Description (optional)</label>
            <textarea
              id="description"
              name="description"
              value={values.description}
              onChange={change}
              maxLength={1000}
              rows={5}
              placeholder="Describe the problem and any useful details."
              aria-invalid={!!errors.description}
            />
            <small>{values.description.length}/1000</small>
            {errors.description && (
              <p className="field-error">{errors.description}</p>
            )}
          </div>
          <div className="report-two-columns">
            {[
              ["category", categories],
              ["priority", ["Low", "Normal", "High"]],
            ].map(([name, options]) => (
              <div className="form-field" key={name}>
                <label htmlFor={name}>
                  {name === "category" ? "Category" : "Priority"}
                </label>
                <select
                  id={name}
                  name={name}
                  value={values[name]}
                  onChange={change}
                  required
                >
                  <option value="" disabled>
                    Choose a category
                  </option>
                  {options.map((value) => (
                    <option key={value}>{value}</option>
                  ))}
                </select>
                {errors[name] && <p className="field-error">{errors[name]}</p>}
              </div>
            ))}
          </div>
          <div className="form-field photo-picker">
            <label htmlFor="photo">Photo (optional)</label>
            <p id="photo-help">
              One JPG, PNG, or WEBP image, up to 5 MB and 20 megapixels.
            </p>
            <input
              ref={fileInput}
              id="photo"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={selectPhoto}
              aria-describedby="photo-help photo-error"
              aria-invalid={!!(photoError || errors.photo)}
            />
            {preview && photo && (
              <div className="photo-preview">
                <img
                  src={preview}
                  alt="Selected report photo preview"
                  onError={() => {
                    removePhoto();
                    setPhotoError(
                      "This image could not be opened. Please choose another photo.",
                    );
                  }}
                />
                <p>{photo.name}</p>
                <button type="button" onClick={removePhoto}>
                  Remove photo
                </button>
              </div>
            )}
            <p className="field-error" id="photo-error" role="alert">
              {photoError || errors.photo}
            </p>
            {errors.photo && (
              <p>
                Choose another photo, retry, or remove it and submit without a
                photo.
              </p>
            )}
          </div>
          <div className="hero-actions">
            <button className="button primary" disabled={busy}>
              {busy ? "Submitting…" : "Submit report"}
            </button>
            <Link className="button secondary" to="/my-reports">
              Cancel
            </Link>
          </div>
        </fieldset>
      </form>
    </section>
  );
}
