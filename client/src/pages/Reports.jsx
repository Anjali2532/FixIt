import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import {
  categories,
  statuses,
  date,
  Message,
  Badge,
} from "../components/ReportUI";

export default function Reports() {
  const { user } = useAuth(),
    location = useLocation();
  const admin = user.role === "Administrator";
  const [filters, setFilters] = useState({
    q: "",
    category: "",
    status: "",
    page: 1,
  });
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
    setFilters((current) => ({
      ...current,
      [event.target.name]: event.target.value,
      page: 1,
    }));
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
      <div className="report-stats">
        {statuses.map((status) => (
          <article key={status}>
            <span>{status}</span>
            <strong>{data ? data.counts[status] : "—"}</strong>
          </article>
        ))}
      </div>
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
      <Message>{error}</Message>
      {error && (
        <button onClick={() => setRetry((n) => n + 1)}>Try again</button>
      )}
      {!data && !error && <p role="status">Loading reports…</p>}
      {data && (
        <>
          <p className="result-count">
            {data.total} {data.total === 1 ? "report" : "reports"} found
          </p>
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
                    <p>{issue.location}</p>
                    <small>{date(issue.created_at)}</small>
                  </div>
                  <Badge status={issue.status} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <h2>
                {filters.q || filters.status || filters.category
                  ? "No matching reports"
                  : "No reports yet"}
              </h2>
              <p>
                {admin
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
