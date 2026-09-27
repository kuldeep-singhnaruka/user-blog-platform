import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { useAuth } from "./auth";
import AuthPages from "./pages/Auth";
import Editor from "./pages/Editor";
import Feed from "./pages/Feed";
import Mine from "./pages/Mine";
import PostPage from "./pages/Post";

function RequireAuth({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return <p className="muted page-note">Loading your desk…</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Feed />} />
        <Route path="/posts/:slug" element={<PostPage />} />
        <Route path="/login" element={<AuthPages mode="login" />} />
        <Route path="/register" element={<AuthPages mode="register" />} />
        <Route path="/write" element={<RequireAuth><Editor /></RequireAuth>} />
        <Route path="/edit/:id" element={<RequireAuth><Editor /></RequireAuth>} />
        <Route path="/me" element={<RequireAuth><Mine /></RequireAuth>} />
        <Route path="*" element={<p className="page-note">That page is not on the shelf.</p>} />
      </Routes>
    </Layout>
  );
}
