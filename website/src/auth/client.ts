// Single isolated place for auth wiring. There is no backend yet — set
// AUTH_ENDPOINT and replace the body of signIn() once one exists.
export const AUTH_ENDPOINT = '';

export interface Credentials {
  email: string;
  password: string;
}

export async function signIn(_credentials: Credentials): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 600));
  throw new Error("Sign-in isn't connected yet — no backend is configured.");
}
