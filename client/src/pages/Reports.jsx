import React, { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import {
  categories,
  statuses,
  date,
  Message,
  Badge,
} from "../components/ReportUI";

import {
  defaultFilters,
  readReportFilters,
  writeReportFilters,
  toggleReportSort,
} from "../reportFilters";

export default function Reports() {
  const { user } = useAuth(),
    location = useLocation();
  const admin = user.role === "Administrator";
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useMemo(
    () => readReportFilters(searchParams),
    [searchParams],
  );
  function setFilters(value, options = {}) {
    const next = typeof value === "function" ? value(filters) : value;
    setSearchParams(writeReportFilters(next), options);
  }
  const matchingFilters = Boolean(
    filters.q ||
    filters.category ||
    filters.status ||
    filters.assignee ||
    filters.attention,
  );
  const sortedColumn = ["newest", "oldest"].includes(filters.sort)
    ? "Submitted"
    : filters.sort.startsWith("status")
      ? "Status"
      : "Category";
  const descending = ["newest", "status-desc", "category-desc"].includes(
    filters.sort,
  );
  const [contacts, setContacts] = useState([]);
  const [staffError, setStaffError] = useState("");
  useEffect(() => {
    let active = true;
    if (admin)
      api("/api/staff")
        .then((result) => {
          if (active) setContacts(result.contacts);
        })
        .catch((problem) => {
          if (active) setStaffError(problem.message);
        });
    return () => {
      active = false;
    };
  }, [admin]);
  const [data, setData] = useState(null),
    [error, setError] = useState(""),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setError("");
    setData(null);
    const timer = setTimeout(
      () =>
        api(`/api/issues?${new URLSearchParams(filters)}`)
          .then((result) => {
            if (active) setData(result);
          })
          .catch((problem) => {
            if (active) setError(problem.message);
          }),
      200,
    );
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [filters, retry]);
  const change = (event) =>
    setFilters(
      (current) => ({
        ...current,
        [event.target.name]: event.target.value,
        page: 1,
      }),
      { replace: event.target.name === "q" },
    );
  return (
    <section className="dashboard-page">
      {location.state?.message && (
        <div className="alert success" role="status">
          {location.state.message}
        </div>
      )}
      <div className="dashboard-heading">
        <div>
          <p className="eyebrow">
            {admin ? "COMMUNITY WORKSPACE" : "YOUR COMMUNITY"}
          </p>
          <h1>{admin ? "Manage reports" : "My Reports"}</h1>
          <p>
            {admin
              ? "Review issues and keep residents informed."
              : "Report a problem and follow its progress."}
          </p>
        </div>
        {!admin && (
          <Link className="button primary" to="/reports/new">
            + Report an issue
          </Link>
        )}
      </div>
      {!admin && data && (
        <p className="open-count">
          {data.counts.Reported +
            data.counts.Assigned +
            data.counts["In Progress"]}{" "}
          open · {data.counts.Resolved} resolved
        </p>
      )}
      <div className="report-stats">
        {statuses.map((status) => (
          <article key={status}>
            <span>{status}</span>
            <strong>{data ? data.counts[status] : "—"}</strong>
          </article>
        ))}
      </div>
      {admin && data?.summary && (
        <section className="admin-overview">
          <button
            className="attention-card"
            onClick={() =>
              setFilters((current) => ({ ...current, attention: "1", page: 1 }))
            }
          >
            <strong>{data.summary.needs_attention}</strong>
            <span>Needs attention</span>
            <small>Open and unassigned, or more than seven days old</small>
          </button>
          <article className="category-summary">
            <h2>Reported categories</h2>
            {data.summary.categories.length ? (
              <ul>
                {data.summary.categories.map((category) => (
                  <li key={category.name}>
                    <span>{category.name}</span>
                    <strong>{category.count}</strong>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No reports yet.</p>
            )}
          </article>
        </section>
      )}
      {!admin && (
        <div className="report-tabs" role="group" aria-label="Report views">
          {[
            ["", "All"],
            ["Open", "Open"],
            ["Resolved", "Resolved"],
          ].map(([value, label]) => (
            <button
              key={label}
              aria-pressed={filters.status === value}
              onClick={() =>
                setFilters((current) => ({
                  ...current,
                  status: value,
                  page: 1,
                }))
              }
            >
              {label}
            </button>
          ))}
        </div>
      )}
      <div className="report-filters">
        <div>
          <label htmlFor="search">Search reports</label>
          <input
            id="search"
            name="q"
            type="search"
            placeholder="Title, description or location"
            value={filters.q}
            onChange={change}
            maxLength={120}
          />
        </div>
        <div>
          <label htmlFor="status">Status</label>
          <select
            id="status"
            name="status"
            value={filters.status}
            onChange={change}
          >
            <option value="">All statuses</option>
            {!admin && <option value="Open">Open</option>}
            {statuses.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="category">Category</label>
          <select
            id="category"
            name="category"
            value={filters.category}
            onChange={change}
          >
            <option value="">All categories</option>
            {categories.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="management-filters">
        {admin && (
          <div>
            <label htmlFor="assigned-filter">Assigned to</label>
            <select
              id="assigned-filter"
              value={filters.assignee}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  assignee: event.target.value,
                  page: 1,
                }))
              }
            >
              <option value="">All staff</option>
              <option value="unassigned">Unassigned</option>
              {contacts.map((contact) => (
                <option key={contact.id} value={contact.id}>
                  {contact.name}
                  {contact.is_active ? "" : " (inactive)"}
                </option>
              ))}
            </select>
          </div>
        )}
        <div>
          <label htmlFor="sort">Sort reports</label>
          <select
            id="sort"
            value={filters.sort}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                sort: event.target.value,
                page: 1,
              }))
            }
          >
            {[
              ["newest", "Newest first"],
              ["oldest", "Oldest first"],
              ["status", "Status: A to Z"],
              ["status-desc", "Status: Z to A"],
              ["category", "Category: A to Z"],
              ["category-desc", "Category: Z to A"],
            ].map(([value, label]) => (
              <option value={value} key={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        {admin && (
          <Link className="button secondary" to="/admin/staff">
            Manage staff contacts
          </Link>
        )}
      </div>
      {filters.attention === "1" && (
        <p role="status">Showing reports that need attention.</p>
      )}
      {(matchingFilters || filters.sort !== "newest" || filters.page !== 1) && (
        <button
          className="clear-filters"
          onClick={() => setFilters(defaultFilters)}
        >
          Clear filters
        </button>
      )}
      <Message>{error || staffError}</Message>
      {error && (
        <button onClick={() => setRetry((n) => n + 1)}>Try again</button>
      )}
      {!data && !error && <p role="status">Loading reports…</p>}
      {data && (
        <>
          <p className="result-count">
            Showing {data.total} of {data.total_all} reports
          </p>
          {data.issues.length > 0 && (
            <div className="report-table-wrap">
              <table
                className={`report-table ${admin ? "admin-report-table" : ""}`}
              >
                <caption className="sr-only">
                  {admin ? "Community reports" : "Your submitted reports"}
                </caption>
                <thead>
                  <tr>
                    {[
                      "Report",
                      "Category",
                      "Location",
                      ...(admin ? ["Reported by"] : []),
                      "Assigned to",
                      "Submitted",
                      "Status",
                    ].map((label) => (
                      <th
                        key={label}
                        scope="col"
                        aria-sort={
                          label === sortedColumn
                            ? descending
                              ? "descending"
                              : "ascending"
                            : undefined
                        }
                      >
                        {["Submitted", "Status", "Category"].includes(label) ? (
                          <button
                            className="table-sort"
                            onClick={() =>
                              setFilters((current) => ({
                                ...current,
                                sort: toggleReportSort(current.sort, label),
                                page: 1,
                              }))
                            }
                            aria-label={`Sort by ${label.toLowerCase()}`}
                          >
                            {label}
                            {label === sortedColumn && (
                              <span className="sort-indicator">
                                {label === "Submitted"
                                  ? descending
                                    ? " (newest)"
                                    : " (oldest)"
                                  : descending
                                    ? " (Z–A)"
                                    : " (A–Z)"}
                              </span>
                            )}
                          </button>
                        ) : (
                          label
                        )}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.issues.map((issue) => (
                    <tr key={issue.id}>
                      <td>
                        <Link to={`/reports/${issue.id}`}>
                          #{issue.id} · {issue.title}
                        </Link>
                        {issue.photo_url && <small>Photo attached</small>}
                      </td>
                      <td>{issue.category}</td>
                      <td>{issue.location}</td>
                      {admin && <td>{issue.reporter}</td>}
                      <td>{issue.assigned_to?.name || "Unassigned"}</td>
                      <td>{date(issue.created_at)}</td>
                      <td>
                        <Badge status={issue.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {data.issues.length ? (
            <div className="report-list">
              {data.issues.map((issue) => (
                <Link
                  className="report-row"
                  key={issue.id}
                  to={`/reports/${issue.id}`}
                >
                  <div>
                    <span className="report-meta">
                      #{issue.id} · {issue.category} · {issue.priority} priority
                    </span>
                    <h2>{issue.title}</h2>
                    {issue.photo_url && (
                      <span className="report-meta">Photo attached</span>
                    )}
                    <p>{issue.location}</p>
                    <p>
                      Assigned to:{" "}
                      {issue.assigned_to?.name || "Not assigned yet"}
                    </p>
                    {admin && <p>Reported by: {issue.reporter}</p>}
                    <small>{date(issue.created_at)}</small>
                  </div>
                  <Badge status={issue.status} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <h2>
                {matchingFilters ? "No matching reports" : "No reports yet"}
              </h2>
              <p>
                {matchingFilters
                  ? "Try different filters or clear them to see more reports."
                  : admin
                    ? "Submitted reports will appear here."
                    : "Use “Report an issue” to let your community know what needs attention."}
              </p>
            </div>
          )}
          {data.total > 20 && (
            <div className="pagination">
              <button
                disabled={filters.page === 1}
                onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}
              >
                Previous
              </button>
              <span>
                Page {data.page} of {Math.ceil(data.total / 20)}
              </span>
              <button
                disabled={filters.page * 20 >= data.total}
                onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
