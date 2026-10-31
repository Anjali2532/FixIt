import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { categories, Message } from "../components/ReportUI";

export default function NewReport() {
  const navigate = useNavigate();
  const [values, setValues] = useState({
    title: "",
    description: "",
    location: "",
    category: "",
    priority: "Normal",
  });
  const [error, setError] = useState(""),
    [errors, setErrors] = useState({}),
    [busy, setBusy] = useState(false);
  const change = (event) =>
    setValues((v) => ({ ...v, [event.target.name]: event.target.value }));
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setErrors({});
    try {
      const result = await api("/api/issues", { method: "POST", body: values });
      navigate(`/reports/${result.issue.id}`, {
        replace: true,
        state: { message: "Your report was submitted successfully." },
      });
    } catch (problem) {
      setError(problem.message);
      setErrors(problem.errors || {});
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="dashboard-page report-form-page">
      <Link to="/my-reports">← My Reports</Link>
      <h1>Report an issue</h1>
      <p className="muted">
        Tell us what happened and where. All fields are required.
      </p>
      <Message>{error}</Message>
      <form className="account-card report-form" onSubmit={submit}>
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
              minLength={name === "title" ? 5 : 3}
              maxLength={name === "title" ? 120 : 200}
              placeholder={
                name === "title"
                  ? "e.g. Broken light in the hallway"
                  : "e.g. Building A, second floor"
              }
              aria-invalid={!!errors[name]}
            />
            {errors[name] && <p className="field-error">{errors[name]}</p>}
          </div>
        ))}
        <div className="form-field">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={values.description}
            onChange={change}
            required
            minLength={20}
            maxLength={3000}
            rows={5}
            placeholder="Describe the problem and any useful details."
            aria-invalid={!!errors.description}
          />
          <small>
            {values.description.length}/3000 · At least 20 characters
          </small>
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
        <div className="hero-actions">
          <button className="button primary" disabled={busy}>
            {busy ? "Submitting…" : "Submit report"}
          </button>
          <Link className="button secondary" to="/my-reports">
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
}
