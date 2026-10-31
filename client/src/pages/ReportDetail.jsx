import React, { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth, dashboardPath } from "../auth";
import { statuses, date, Message, Badge } from "../components/ReportUI";

export default function ReportDetail() {
  const { id } = useParams(),
    { user } = useAuth(),
    location = useLocation();
  const [data, setData] = useState(null),
    [error, setError] = useState(""),
    [retry, setRetry] = useState(0);
  const [status, setStatus] = useState("Reported"),
    [note, setNote] = useState(""),
    [busy, setBusy] = useState(false),
    [saved, setSaved] = useState("");
  useEffect(() => {
    let active = true;
    setData(null);
    setError("");
    api(`/api/issues/${id}`)
      .then((result) => {
        if (active) {
          setData(result);
          setStatus(result.issue.status);
        }
      })
      .catch((problem) => {
        if (active) setError(problem.message);
      });
    return () => {
      active = false;
    };
  }, [id, retry]);
  async function update(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setSaved("");
    try {
      await api(`/api/issues/${id}`, {
        method: "PATCH",
        body: { status, note },
      });
      setNote("");
      setSaved("Progress update saved.");
      setRetry((n) => n + 1);
    } catch (problem) {
      setError(problem.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="dashboard-page">
      <Link to={dashboardPath(user)}>← Back to reports</Link>
      <Message>{error}</Message>
      {error && !data && (
        <button onClick={() => setRetry((n) => n + 1)}>Try again</button>
      )}
      {(saved || location.state?.message) && (
        <div className="alert success" role="status">
          {saved || location.state.message}
        </div>
      )}
      {!data && !error && <p role="status">Loading report…</p>}
      {data && (
        <>
          <div className="dashboard-heading">
            <div>
              <p className="eyebrow">REPORT #{data.issue.id}</p>
              <h1>{data.issue.title}</h1>
              <p>Submitted {date(data.issue.created_at)}</p>
            </div>
            <Badge status={data.issue.status} />
          </div>
          <div className="dashboard-grid">
            <article className="account-card report-description">
              <h2>Issue details</h2>
              <div className="report-meta">
                {data.issue.category} · {data.issue.priority} priority
              </div>
              <h3>Location</h3>
              <p>{data.issue.location}</p>
              <h3>Description</h3>
              <p>{data.issue.description}</p>
            </article>
            <article className="account-card">
              <h2>Progress history</h2>
              <ol className="report-timeline">
                {data.updates.map((item) => (
                  <li key={item.id}>
                    <Badge status={item.status} />
                    <p>{item.note}</p>
                    <small>{date(item.created_at)}</small>
                  </li>
                ))}
              </ol>
            </article>
          </div>
          {user.role === "Administrator" && (
            <form
              className="account-card report-form admin-update"
              onSubmit={update}
            >
              <h2>Update progress</h2>
              <div className="form-field">
                <label htmlFor="new-status">Status</label>
                <select
                  id="new-status"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  {statuses.map((value) => (
                    <option key={value}>{value}</option>
                  ))}
                </select>
              </div>
              <div className="form-field">
                <label htmlFor="note">Progress note</label>
                <textarea
                  id="note"
                  rows={3}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  required
                  minLength={5}
                  maxLength={1000}
                  placeholder="Explain what has changed. This note is visible to the resident."
                />
              </div>
              <button className="button primary" disabled={busy}>
                {busy ? "Saving…" : "Save update"}
              </button>
            </form>
          )}
        </>
      )}
    </section>
  );
}
