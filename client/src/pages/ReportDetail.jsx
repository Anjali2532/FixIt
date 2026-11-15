import React, { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api } from "../api";
import ReportPhoto from "../components/ReportPhoto";
import { useAuth, dashboardPath } from "../auth";
import { date, Message, Badge } from "../components/ReportUI";

export default function ReportDetail() {
  const { id } = useParams(),
    { user } = useAuth(),
    location = useLocation();
  const admin = user.role === "Administrator";
  const [data, setData] = useState(null),
    [error, setError] = useState(""),
    [retry, setRetry] = useState(0);
  const [status, setStatus] = useState("Reported"),
    [note, setNote] = useState(""),
    [busy, setBusy] = useState(false),
    [saved, setSaved] = useState("");
  const [contacts, setContacts] = useState([]),
    [staffId, setStaffId] = useState(""),
    [assignmentNote, setAssignmentNote] = useState("");
  useEffect(() => {
    let active = true;
    setData(null);
    setError("");
    api(`/api/issues/${id}`)
      .then((result) => {
        if (active) {
          setData(result);
          setStatus(result.issue.status);
          setStaffId(String(result.issue.assigned_to?.id || ""));
        }
      })
      .catch((problem) => {
        if (active) setError(problem.message);
      });
    if (admin)
      api("/api/staff")
        .then((result) => {
          if (active) setContacts(result.contacts);
        })
        .catch((problem) => {
          if (active) setError(problem.message);
        });
    return () => {
      active = false;
    };
  }, [id, retry, admin]);
  async function save(event, action) {
    event.preventDefault();
    if (busy || !data) return;
    setBusy(true);
    setError("");
    setSaved("");
    const path =
      action === "assignment"
        ? `/api/issues/${id}/assignment`
        : action === "note"
          ? `/api/issues/${id}/notes`
          : `/api/issues/${id}`;
    const body =
      action === "assignment"
        ? {
            staff_id: Number(staffId),
            note: assignmentNote,
            version: data.issue.version,
          }
        : { status, note, version: data.issue.version };
    try {
      const result = await api(path, {
        method: action === "status" ? "PATCH" : "POST",
        body,
      });
      setSaved(result.message);
      setNote("");
      setAssignmentNote("");
      setRetry((value) => value + 1);
    } catch (problem) {
      setError(problem.message);
      setStatus(data.issue.status);
    } finally {
      setBusy(false);
    }
  }
  const transitions = {
    Reported: ["Assigned", "Resolved"],
    Assigned: ["In Progress", "Resolved"],
    "In Progress": ["Resolved"],
    Resolved: ["In Progress", "Reported"],
  };
  return (
    <section className="dashboard-page">
      <Link to={dashboardPath(user)}>← Back to reports</Link>
      <Message>{error}</Message>
      {error && (
        <button onClick={() => setRetry((value) => value + 1)}>
          Reload latest report
        </button>
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
              {admin && <p>Reported by {data.issue.reporter}</p>}
              {admin && data.issue.status !== "Resolved" && (
                <p>
                  Open for{" "}
                  {Math.max(
                    0,
                    Math.floor(
                      (Date.now() - new Date(data.issue.created_at).getTime()) /
                        86400000,
                    ),
                  )}{" "}
                  days
                </p>
              )}
            </div>
            <Badge status={data.issue.status} />
          </div>
          <div className="assignment-summary">
            <strong>Assigned to:</strong>{" "}
            {data.issue.assigned_to
              ? `${data.issue.assigned_to.name} · ${data.issue.assigned_to.team}`
              : "Not assigned yet"}
            {data.issue.assigned_to && !data.issue.assigned_to.is_active && (
              <span> (contact inactive)</span>
            )}
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
              <p>
                {data.issue.description ||
                  "No additional description provided."}
              </p>
              {data.issue.photo_url && (
                <ReportPhoto
                  key={data.issue.photo_url}
                  src={data.issue.photo_url}
                  title={data.issue.title}
                />
              )}
            </article>
            <article className="account-card">
              <h2>Progress history</h2>
              <ol className="report-timeline">
                {data.updates.map((item) => (
                  <li key={item.id}>
                    <Badge status={item.status} />
                    <p className="history-action">
                      {item.action === "Created"
                        ? "Report created"
                        : item.action === "StatusChanged"
                          ? "Status changed"
                          : item.action === "Reassigned"
                            ? "Reassigned"
                            : item.action === "Assigned"
                              ? "Assigned"
                              : "Progress note"}
                    </p>
                    {item.old_value && item.new_value && (
                      <small>
                        {item.old_value} → {item.new_value}
                      </small>
                    )}
                    {item.action === "Assigned" && !item.old_value && (
                      <small>{item.new_value}</small>
                    )}
                    <p>{item.note}</p>
                    <small>
                      {date(item.created_at)}
                      {admin && item.changed_by ? ` · ${item.changed_by}` : ""}
                    </small>
                  </li>
                ))}
              </ol>
            </article>
          </div>
          {admin && (
            <div className="admin-controls">
              <form
                className="account-card report-form"
                onSubmit={(event) => save(event, "assignment")}
              >
                <h2>Assignment</h2>
                <p className="muted">Choose who will handle this report.</p>
                <div className="form-field">
                  <label htmlFor="assignee">Assign to</label>
                  <select
                    id="assignee"
                    value={staffId}
                    onChange={(event) => setStaffId(event.target.value)}
                    required
                    disabled={busy || data.issue.status === "Resolved"}
                  >
                    <option value="">Choose a staff member</option>
                    {contacts.map((contact) => (
                      <option
                        key={contact.id}
                        value={contact.id}
                        disabled={!contact.is_active}
                      >
                        {contact.name} · {contact.team}
                        {!contact.is_active ? " (inactive)" : ""}
                      </option>
                    ))}
                  </select>
                </div>
                {!contacts.some((contact) => contact.is_active) && (
                  <p>
                    No active staff contacts.{" "}
                    <Link to="/admin/staff">Add a staff contact</Link> first.
                  </p>
                )}
                <div className="form-field">
                  <label htmlFor="assignment-note">
                    Assignment note (optional)
                  </label>
                  <textarea
                    id="assignment-note"
                    rows={3}
                    value={assignmentNote}
                    onChange={(event) => setAssignmentNote(event.target.value)}
                    maxLength={1000}
                    disabled={busy}
                  />
                </div>
                {data.issue.status === "Resolved" && (
                  <p>Reopen the report before changing its assignment.</p>
                )}
                <button
                  className="button primary"
                  disabled={busy || data.issue.status === "Resolved"}
                >
                  {busy ? "Saving…" : "Save assignment"}
                </button>
                <p>
                  <Link to="/admin/staff">Manage staff contacts</Link>
                </p>
              </form>
              <form
                className="account-card report-form"
                onSubmit={(event) => save(event, "status")}
              >
                <h2>Update progress</h2>
                <div className="form-field">
                  <label htmlFor="new-status">Status</label>
                  <select
                    id="new-status"
                    value={status}
                    onChange={(event) => setStatus(event.target.value)}
                    disabled={busy}
                  >
                    {[data.issue.status, ...transitions[data.issue.status]].map(
                      (value) => (
                        <option
                          key={value}
                          disabled={
                            ["Assigned", "In Progress"].includes(value) &&
                            !data.issue.assigned_to
                          }
                        >
                          {value}
                        </option>
                      ),
                    )}
                  </select>
                </div>
                <div className="form-field">
                  <label htmlFor="note">Progress note</label>
                  <textarea
                    id="note"
                    rows={4}
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                    minLength={5}
                    maxLength={1000}
                    required={status !== data.issue.status}
                    disabled={busy}
                    placeholder="Explain what changed. A resolution must describe the fix."
                  />
                </div>
                <div className="hero-actions">
                  <button className="button primary" disabled={busy}>
                    {busy ? "Saving…" : "Save update"}
                  </button>
                  <button
                    type="button"
                    className="button secondary"
                    disabled={busy || note.trim().length < 5}
                    onClick={(event) => save(event, "note")}
                  >
                    Add note only
                  </button>
                </div>
              </form>
            </div>
          )}
        </>
      )}
    </section>
  );
}
