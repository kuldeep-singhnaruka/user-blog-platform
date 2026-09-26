import { useEffect, useState } from "react";
import { api } from "../api";

export default function Admin() {
  const [audit, setAudit] = useState(null);
  const [users, setUsers] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api("/api/v1/admin/audit"),
      api("/api/v1/admin/users"),
      api("/api/v1/admin/permissions"),
      api("/api/v1/admin/query-plan"),
    ])
      .then(([auditPage, userRows, permissionRows, queryPlan]) => {
        setAudit(auditPage);
        setUsers(userRows);
        setPermissions(permissionRows);
        setPlan(queryPlan);
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="error page-note">{error}</p>;
  if (!audit) return <p className="muted page-note">Loading the oversight desk…</p>;

  const grouped = permissions.reduce((acc, row) => {
    acc[row.role] = acc[row.role] || [];
    acc[row.role].push(row.permission);
    return acc;
  }, {});

  return (
    <section className="admin">
      <p className="eyebrow">Least privilege</p>
      <h1>Oversight</h1>
      <div className="split">
        <div>
          <h2>Roles</h2>
          {Object.entries(grouped).map(([role, list]) => (
            <article key={role} className="role-card">
              <h3>{role}</h3>
              <p>{list.join(" · ")}</p>
            </article>
          ))}
        </div>
        <div>
          <h2>Accounts</h2>
          <ul className="plain">
            {users.map((account) => (
              <li key={account.id}>
                <strong>{account.display_name}</strong>
                <span>{account.role}</span>
                <em>{account.email}</em>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <h2>Audit log</h2>
      <table className="desk">
        <thead>
          <tr>
            <th>When</th>
            <th>Action</th>
            <th>Resource</th>
          </tr>
        </thead>
        <tbody>
          {audit.data.map((row) => (
            <tr key={row.id}>
              <td>{new Date(row.created_at).toLocaleString()}</td>
              <td>{row.action}</td>
              <td>
                {row.resource_type} {row.resource_id}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {plan && (
        <>
          <h2>Query plan</h2>
          <p className="muted">{plan.index_hint}</p>
          <pre>{plan.sql}</pre>
          <pre>{JSON.stringify(plan.plan, null, 2)}</pre>
        </>
      )}
    </section>
  );
}
