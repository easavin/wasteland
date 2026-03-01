import { NextRequest } from "next/server";

// Re-export JWT functions so existing imports keep working
export { createToken, verifyToken } from "./jwt";

const SALT_ROUNDS = 12;

export async function hashPassword(password: string): Promise<string> {
  const { hash } = await import("bcryptjs");
  return hash(password, SALT_ROUNDS);
}

export async function verifyPassword(
  password: string,
  passwordHash: string
): Promise<boolean> {
  const { compare } = await import("bcryptjs");
  return compare(password, passwordHash);
}

export async function getSession(
  request: NextRequest
): Promise<{ sub: string; email: string; role: string } | null> {
  const { verifyToken } = await import("./jwt");
  const token = request.cookies.get("admin_token")?.value;
  if (!token) return null;
  return verifyToken(token);
}
