import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function AuthPages({ mode }) {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const isRegister = mode === "register";

  if (user) return <Navigate to="/me" replace />;

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      if (isRegister) await register(email, password, displayName);
      else await login(email, password);
      navigate("/me");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="auth-card">
      <p className="eyebrow">{isRegister ? "New desk" : "Welcome back"}</p>
      <h1>{isRegister ? "Create your blog" : "Sign in"}</h1>
      <form onSubmit={submit}>
        {isRegister && (
          <label>
            Display name
            <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} required minLength={2} />
          </label>
        )}
        <label>
          Email
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            minLength={8}
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="button" type="submit">
          {isRegister ? "Create account" : "Sign in"}
        </button>
      </form>
      {isRegister ? (
        <p className="muted">
          Already writing here? <Link to="/login">Sign in</Link>
        </p>
      ) : (
        <p className="muted">
          New here? <Link to="/register">Create an account</Link>
        </p>
      )}
      {!isRegister && (
        <aside className="demo-accounts">
          <p>Demo accounts</p>
          <ul>
            <li>mina@fieldnotes.local / Author123!</li>
            <li>ravi@fieldnotes.local / Reader123!</li>
            <li>admin@fieldnotes.local / Admin123!</li>
          </ul>
        </aside>
      )}
    </section>
  );
}
