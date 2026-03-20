import { useContext } from "react";
import { AuthContext } from "./AuthProvider";

export function useAuth() {
  return useContext(AuthContext);
}
