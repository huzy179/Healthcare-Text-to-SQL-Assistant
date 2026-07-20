import { NextResponse } from "next/server";

import { listUsers } from "@/lib/users";

export async function GET() {
  return NextResponse.json({ users: listUsers() });
}
