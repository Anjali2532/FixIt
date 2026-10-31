import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { api } from "./api";
const Context = createContext(null);
export const dashboardPath = (user) =>
  user.role === "Administrator" ? "/admin/dashboard" : "/my-reports";
export const useAuth = () => useContext(Context);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null),
    [status, setStatus] = useState("loading"),
    [notice, setNotice] = useState("");
  const generation = useRef(0);
  const refresh = useCallback(async () => {
    const request = ++generation.current;
    try {
      const data = await api("/api/auth/me");
      if (request === generation.current) {
        setUser(data.user);
        setStatus("ready");
      }
    } catch (error) {
      if (request === generation.current) {
        setUser(null);
        setStatus(error.status === 401 ? "ready" : "error");
      }
    }
  }, []);
  useEffect(() => {
    refresh();
    const expired = () => {
      generation.current++;
      setUser(null);
      setStatus("ready");
      setNotice("Your session has expired. Please log in again.");
    };
    const sync = (event) => {
      if (event.key === "fixit-auth-event") refresh();
    };
    window.addEventListener("fixit:session-expired", expired);
    window.addEventListener("focus", refresh);
    window.addEventListener("pageshow", refresh);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("fixit:session-expired", expired);
      window.removeEventListener("focus", refresh);
      window.removeEventListener("pageshow", refresh);
      window.removeEventListener("storage", sync);
    };
  }, [refresh]);
  const notify = () => {
    try {
      localStorage.setItem("fixit-auth-event", String(Date.now()));
    } catch {
      /* Storage is optional. */
    }
  };
  const signedIn = (account) => {
    generation.current++;
    setUser(account);
    setStatus("ready");
    setNotice("");
    notify();
  };
  const logout = async () => {
    await api("/api/auth/logout", { method: "POST" });
    generation.current++;
    setUser(null);
    setStatus("ready");
    setNotice("");
    notify();
  };
  return (
    <Context.Provider
      value={{ user, status, notice, refresh, signedIn, logout }}
    >
      {children}
    </Context.Provider>
  );
}
