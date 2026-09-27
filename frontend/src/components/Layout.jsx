import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../auth";

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  return (
    <div className="frame">
      <header className="topbar">
        <Link to="/" className="brand"><i />Fieldnotes</Link>
        <nav>
          <NavLink to="/" end>Reading room</NavLink>
          {user && <NavLink to="/write">Write</NavLink>}
          {user && <NavLink to="/me">My desk</NavLink>}
        </nav>
        <div className="account">
          {user ? (
            <>
              <span className="who">{user.display_name}</span>
              <button type="button" className="text-button" onClick={logout}>Sign out</button>
            </>
          ) : (
            <>
              <Link to="/login">Sign in</Link>
              <Link to="/register" className="button small">Create account</Link>
            </>
          )}
        </div>
      </header>
      <main className="shell">{children}</main>
    </div>
  );
}
