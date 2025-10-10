import { api } from "./client";
export type User = { id:number; email:string; full_name?:string|null; is_active:boolean; role:"admin"|"manager"|"customer"; };
export type UserCreate = { email:string; full_name?:string|null; is_active?:boolean; role?:User["role"]; password:string; };
export type UserUpdate = Partial<Omit<UserCreate,"password">> & { password?: string };

export async function listUsers(params?: { skip?: number; limit?: number }) { const {data}=await api.get<User[]>("/admin/users",{params}); return data; }
export async function getUser(id:number){ const {data}=await api.get<User>(\`/admin/users/\${id}\`); return data; }
export async function createUser(payload:UserCreate){ const {data}=await api.post<User>("/admin/users",payload); return data; }
export async function updateUser(id:number,payload:UserUpdate){ const {data}=await api.put<User>(\`/admin/users/\${id}\`,payload); return data; }
export async function deleteUser(id:number){ await api.delete(\`/admin/users/\${id}\`); }
