import React, { useEffect, useState } from "react";
import {
  BrowserRouter,
  Link,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import Reports from "./pages/Reports";
import NewReport from "./pages/NewReport";
import ReportDetail from "./pages/ReportDetail";
import Home from "./pages/Home";
import AuthForm from "./pages/AuthForm";
import Alert from "./components/Alert";
import { AuthProvider, dashboardPath, useAuth } from "./auth";

function Layout() {
  const { user, logout } = useAuth(),
    navigate = useNavigate(),
    location = useLocation();
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    setError("");
    window.scrollTo(0, 0);
  }, [location.pathname]);
  async function handleLogout() {
    setBusy(true);
    setError("");
    try {
      // Go home first so the protected page does not redirect during logout.
      navigate("/", { replace: true });
      await logout();
      navigate("/", {
        replace: true,
        state: { message: "You have been logged out." },
      });
    } catch (problem) {
      setError(problem.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <header className="nav">
        <Link className="brand" to="/" aria-label="FixIt home">
          <span className="brand-mark">F</span>FixIt
        </Link>
        <nav className="nav-links" aria-label="Main navigation">
          {user ? (
            <>
              <Link to={dashboardPath(user)}>
                {user.role === "Administrator" ? "Dashboard" : "My Reports"}
              </Link>
              <span className="nav-name">{user.name}</span>
              {user.role === "Administrator" && (
                <span className="role-badge">Admin</span>
              )}
              <button onClick={handleLogout} disabled={busy}>
                {busy ? "Logging out…" : "Log Out"}
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Log In</Link>
              <Link className="button primary small" to="/signup">
                Create Account
              </Link>
            </>
          )}
        </nav>
      </header>
      {error && (
        <div className="global-alert">
          <Alert>{error}</Alert>
        </div>
      )}
      <main>
        <Outlet />
      </main>
      <footer>
        <span>FixIt</span>
      </footer>
    </>
  );
}

function Protected({ role }) {
  const { user, status, refresh } = useAuth(),
    location = useLocation();
  if (status === "loading")
    return (
      <div className="loading-page" role="status">
        Checking your account…
      </div>
    );
  if (status === "error")
    return (
      <section className="message-page">
        <h1>We couldn’t check your account.</h1>
        <p>Please check your connection and try again.</p>
        <button onClick={refresh}>Try again</button>
      </section>
    );
  if (!user)
    return (
      <Navigate
        to={`/login?next=${encodeURIComponent(location.pathname)}`}
        replace
      />
    );
  if (user.role !== role)
    return (
      <Navigate
        to={dashboardPath(user)}
        replace
        state={{ message: "You do not have permission to access that page." }}
      />
    );
  return <Outlet />;
}

function AuthenticatedReport() {
  const { user, status } = useAuth();
  if (status === "loading") return <p role="status">Checking your account…</p>;
  if (status === "error")
    return (
      <section className="message-page">
        <p>We couldn’t check your account.</p>
        <Link to="/">Back to home</Link>
      </section>
    );
  return user ? <ReportDetail /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="signup" element={<AuthForm key="signup" signup />} />
            <Route path="login" element={<AuthForm key="login" />} />
            <Route element={<Protected role="Resident" />}>
              <Route path="my-reports" element={<Reports />} />
              <Route path="reports/new" element={<NewReport />} />
            </Route>
            <Route element={<Protected role="Administrator" />}>
              <Route path="admin/dashboard" element={<Reports />} />
            </Route>
            <Route path="reports/:id" element={<AuthenticatedReport />} />
            <Route
              path="*"
              element={
                <section className="message-page">
                  <h1>Page not found</h1>
                  <p>This page does not exist.</p>
                  <Link className="button primary" to="/">
                    Back to FixIt
                  </Link>
                </section>
              }
            />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
