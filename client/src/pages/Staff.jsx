import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Message } from "../components/ReportUI";

export default function Staff() {
  const [contacts, setContacts] = useState(null),
    [name, setName] = useState(""),
    [team, setTeam] = useState("");
  const [error, setError] = useState(""),
    [saved, setSaved] = useState(""),
    [busy, setBusy] = useState(false),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
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
  }, [retry]);
  async function save(event, contact) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setSaved("");
    try {
      await api(contact ? `/api/staff/${contact.id}` : "/api/staff", {
        method: contact ? "PATCH" : "POST",
        body: contact ? { is_active: !contact.is_active } : { name, team },
      });
      setSaved(contact ? "Staff contact updated." : "Staff contact added.");
      if (!contact) {
        setName("");
        setTeam("");
      }
      setRetry((value) => value + 1);
    } catch (problem) {
      setError(problem.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="dashboard-page">
      <Link to="/admin/dashboard">← Back to reports</Link>
      <h1>Staff contacts</h1>
      <p className="muted">
        Keep the people responsible for maintenance in one place. Contacts do
        not receive login accounts.
      </p>
      <Message>{error}</Message>
      {error && (
        <button
          onClick={() => {
            setError("");
            setRetry((value) => value + 1);
          }}
        >
          Try again
        </button>
      )}
      {saved && (
        <div className="alert success" role="status">
          {saved}
        </div>
      )}
      <div className="dashboard-grid">
        <form
          className="account-card report-form"
          onSubmit={(event) => save(event)}
        >
          <h2>Add staff contact</h2>
          <div className="form-field">
            <label htmlFor="staff-name">Full name</label>
            <input
              id="staff-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={100}
              required
              disabled={busy}
            />
          </div>
          <div className="form-field">
            <label htmlFor="staff-team">Team or responsibility</label>
            <input
              id="staff-team"
              value={team}
              onChange={(event) => setTeam(event.target.value)}
              maxLength={80}
              placeholder="e.g. Maintenance"
              required
              disabled={busy}
            />
          </div>
          <button className="button primary" disabled={busy}>
            {busy ? "Saving…" : "Add contact"}
          </button>
        </form>
        <article className="account-card">
          <h2>Current contacts</h2>
          {!contacts ? (
            <p role="status">Loading contacts…</p>
          ) : !contacts.length ? (
            <p>No staff contacts yet. Add the first person using the form.</p>
          ) : (
            <ul className="staff-list">
              {contacts.map((contact) => (
                <li key={contact.id}>
                  <div>
                    <strong>{contact.name}</strong>
                    <p>
                      {contact.team} ·{" "}
                      {contact.is_active ? "Active" : "Inactive"}
                    </p>
                  </div>
                  <button
                    disabled={busy}
                    onClick={(event) => save(event, contact)}
                    aria-label={`${contact.is_active ? "Deactivate" : "Activate"} ${contact.name}`}
                  >
                    {contact.is_active ? "Deactivate" : "Activate"}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>
    </section>
  );
}
