import { Navigate, Outlet } from "react-router-dom";
export default function ProtectedRoute() {
  const authed = !!localStorage.getItem("auth_token");
  return authed ? <Outlet /> : <Navigate to="/login" replace />;
}
