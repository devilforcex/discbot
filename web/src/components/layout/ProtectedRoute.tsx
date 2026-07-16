import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../../hooks/use-auth-store";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const location = useLocation();

  if (!token) {
    return <Navigate to={`/?connect=1&from=${encodeURIComponent(location.pathname)}`} replace />;
  }

  return <>{children}</>;
}
