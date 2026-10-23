export type Session = {user: {id: string; email: string; first_name: string; last_name: string}; expires_at: string};
export class ApiError extends Error {
  status: number;
  fields: Record<string,string[]>;
  constructor(message: string, status: number, fields: Record<string,string[]> = {}) {super(message);this.status=status;this.fields=fields;}
}
export async function authRequest(route: string, data?: Record<string, string>): Promise<unknown> {
  const headers: Record<string,string> = {};
  if (data) {
    const csrf = await fetch('/api/v1/auth/csrf', {cache:'no-store', credentials:'same-origin'});
    if (!csrf.ok) throw new Error('Service indisponible. Réessayez.');
    headers['X-CSRFToken'] = (await csrf.json()).csrf_token;
    headers['Content-Type'] = 'application/json';
  }
  const response = await fetch('/api/v1/auth/'+route, {method: data ? 'POST':'GET', headers,
    body: data ? JSON.stringify(data):undefined, credentials:'same-origin', cache:'no-store'});
  let body;
  try {body=await response.json();} catch {throw new Error('Service indisponible. Réessayez.');}
  if (!response.ok) throw new ApiError(body.error?.message || 'Service indisponible. Réessayez.',response.status,body.error?.fields);
  return body;
}
