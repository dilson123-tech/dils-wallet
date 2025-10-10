import { Navigate } from "react-router-dom";
export default function Guard({children}:{children:JSX.Element}){
  const t = localStorage.getItem("aurea_token");
  if(!t) return <Navigate to="/login" replace />;
  return children;
}
