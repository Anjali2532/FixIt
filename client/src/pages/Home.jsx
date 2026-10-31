import React from "react";
import { Link, useLocation } from "react-router-dom";
import { dashboardPath, useAuth } from "../auth";
import Alert from "../components/Alert";

export default function Home() {
  const { user } = useAuth(),
    location = useLocation();
  return (
    <>
      <div className="home-message">
        <Alert success>{location.state?.message}</Alert>
      </div>
      <section className="hero">
        <p className="eyebrow">REPORT IT. TRACK IT. GET IT FIXED.</p>
        <h1>
          A better way to care
          <br />
          for your community.
        </h1>
        <p className="intro">
          A broken light. A leaking pipe. A problem that needs attention. FixIt
          brings your community’s reports and updates together in one place.
        </p>
        {user && (
          <div className="hero-actions">
            <Link className="button primary" to={dashboardPath(user)}>
              Open my dashboard <span aria-hidden="true">→</span>
            </Link>
          </div>
        )}
        <p className="release-note">
          Report a problem. Follow updates. Help your community stay in good
          shape.
        </p>
      </section>
      <section className="features" aria-label="How FixIt works">
        {[
          [
            "01",
            "Report a problem",
            "Describe the issue, choose a category and share its location.",
          ],
          [
            "02",
            "Follow the progress",
            "See updates as your report moves toward resolution.",
          ],
          [
            "03",
            "Keep work organized",
            "Administrators can review reports and keep progress up to date.",
          ],
        ].map(([number, title, description]) => (
          <article className="feature" key={number}>
            <span className="number">{number}</span>
            <h2>{title}</h2>
            <p>{description}</p>
          </article>
        ))}
      </section>
      <section className="progress">
        <h2>One report. Clear progress.</h2>
        <ol>
          {["Reported", "In Progress", "Resolved"].map((status) => (
            <li key={status}>{status}</li>
          ))}
        </ol>
      </section>
    </>
  );
}
