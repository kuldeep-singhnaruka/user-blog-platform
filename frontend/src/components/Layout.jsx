import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../auth";

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">
          Fieldnotes
        </Link>
        <nav>
          <NavLink to="/" end>
            Reading room
          </NavLink>
          {user && <NavLink to="/write">Write</NavLink>}
          {user && <NavLink to="/me">My desk</NavLink>}
          {user?.role === "admin" && <NavLink to="/admin">Admin</NavLink>}
        </nav>
        <div className="account">
          {user ? (
            <>
              <span className="who">
                {user.display_name}
                <em>{user.role}</em>
              </span>
              <button type="button" className="text-button" onClick={logout}>
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Sign in</Link>
              <Link to="/register" className="button small">
                Create account
              </Link>
            </>
          )}
        </div>
      </header>
      <main>{children}</main>
      <footer>
        <span>Public essays. Private drafts.</span>
        <a href="/docs">API docs</a>
      </footer>
    </div>
  );
}
