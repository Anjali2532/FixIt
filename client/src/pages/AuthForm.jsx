import React, { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api } from "../api";
import { dashboardPath, useAuth } from "../auth";
import Alert from "../components/Alert";

function Field({
  name,
  label,
  value,
  onChange,
  error,
  type = "text",
  autoComplete,
  maxLength,
  children,
}) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="form-field">
      <label htmlFor={name}>{label}</label>
      <div className="input-wrap">
        <input
          id={name}
          name={name}
          type={type === "password" && visible ? "text" : type}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          maxLength={maxLength}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${name}-error` : undefined}
        />
        {type === "password" && (
          <button
            className="password-toggle"
            type="button"
            aria-label={`${visible ? "Hide" : "Show"} ${label.toLowerCase()}`}
            onClick={() => setVisible((current) => !current)}
          >
            {visible ? "Hide" : "Show"}
          </button>
        )}
      </div>
      {error && (
        <p className="field-error" id={`${name}-error`}>
          {error}
        </p>
      )}
      {children}
    </div>
  );
}

function validation(values, signup) {
  const errors = {};
  if (signup && (!values.name.trim() || values.name.trim().length > 100))
    errors.name = "Enter your name using 1–100 characters.";
  if (
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim()) ||
    values.email.trim().length > 255
  )
    errors.email = "Please enter a valid email address.";
  if (!values.password) errors.password = "Password is required.";
  if (
    signup &&
    (values.password.length < 8 ||
      values.password.length > 128 ||
      !/[A-Za-z]/.test(values.password) ||
      !/[0-9]/.test(values.password))
  )
    errors.password =
      "Use 8–128 characters with at least one letter and one number.";
  if (signup && values.confirm_password !== values.password)
    errors.confirm_password = "Passwords do not match.";
  return errors;
}

export default function AuthForm({ signup = false }) {
  const { user, signedIn, notice } = useAuth(),
    navigate = useNavigate();
  const [values, setValues] = useState({
    name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [errors, setErrors] = useState({}),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false),
    [submitted, setSubmitted] = useState(false);
  if (user) return <Navigate to={dashboardPath(user)} replace />;
  function change(event) {
    const next = { ...values, [event.target.name]: event.target.value };
    setValues(next);
    if (submitted) setErrors(validation(next, signup));
  }
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setSubmitted(true);
    setMessage("");
    const issues = validation(values, signup);
    setErrors(issues);
    if (Object.keys(issues).length) {
      document.getElementById(Object.keys(issues)[0])?.focus();
      return;
    }
    setBusy(true);
    try {
      const data = await api(
        signup ? "/api/auth/register" : "/api/auth/login",
        { method: "POST", body: values },
      );
      signedIn(data.user);
      // Send each user to the dashboard for their role.
      navigate(dashboardPath(data.user), {
        replace: true,
        state: {
          message: signup
            ? `Welcome, ${data.user.name}! Your account is ready.`
            : null,
        },
      });
    } catch (problem) {
      setMessage(problem.message);
      setErrors(problem.errors || {});
      setValues((current) => ({
        ...current,
        password: "",
        confirm_password: "",
      }));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="auth-layout">
      <aside className="auth-intro">
        <p className="eyebrow">YOUR COMMUNITY. ONE PLACE.</p>
        <h1>
          {signup ? "Start with a simple account." : "Welcome back to FixIt."}
        </h1>
        <p>
          {signup
            ? "Create your resident account so you’re ready to report problems and follow their progress."
            : "Log in to your account and stay connected to what’s happening in your community."}
        </p>
        <div className="auth-note">
          <span aria-hidden="true">✓</span>
          <p>
            Your password is securely hashed. Your account details stay private.
          </p>
        </div>
      </aside>
      <div className="auth-card">
        <h2>{signup ? "Create your account" : "Log in"}</h2>
        <p className="form-subtitle">
          {signup
            ? "All fields are required."
            : "Enter your email and password to continue."}
        </p>
        <Alert>{message || (!signup ? notice : "")}</Alert>
        <form onSubmit={submit} noValidate>
          {signup && (
            <Field
              name="name"
              label="Full name"
              value={values.name}
              onChange={change}
              error={errors.name}
              autoComplete="name"
              maxLength={100}
            />
          )}
          <Field
            name="email"
            label="Email address"
            type="email"
            value={values.email}
            onChange={change}
            error={errors.email}
            autoComplete="email"
            maxLength={255}
          />
          <Field
            name="password"
            label="Password"
            type="password"
            value={values.password}
            onChange={change}
            error={errors.password}
            autoComplete={signup ? "new-password" : "current-password"}
            maxLength={128}
          >
            {signup && (
              <ul className="password-rules" aria-label="Password requirements">
                {[
                  [
                    values.password.length >= 8 &&
                      values.password.length <= 128,
                    "8–128 characters",
                  ],
                  [/[A-Za-z]/.test(values.password), "At least one letter"],
                  [/[0-9]/.test(values.password), "At least one number"],
                ].map(([met, rule]) => (
                  <li className={met ? "met" : ""} key={rule}>
                    <span aria-hidden="true">{met ? "✓" : "○"}</span> {rule}
                  </li>
                ))}
              </ul>
            )}
          </Field>
          {signup && (
            <Field
              name="confirm_password"
              label="Confirm password"
              type="password"
              value={values.confirm_password}
              onChange={change}
              error={errors.confirm_password}
              autoComplete="new-password"
              maxLength={128}
            />
          )}
          <button
            className="button primary form-submit"
            type="submit"
            disabled={busy}
          >
            {busy
              ? signup
                ? "Creating account…"
                : "Logging in…"
              : signup
                ? "Create Account"
                : "Log In"}
          </button>
        </form>
        <p className="form-switch">
          {signup ? "Already have an account?" : "New to FixIt?"}{" "}
          <Link to={signup ? "/login" : "/signup"}>
            {signup ? "Log in" : "Create an account"}
          </Link>
        </p>
      </div>
    </section>
  );
}
