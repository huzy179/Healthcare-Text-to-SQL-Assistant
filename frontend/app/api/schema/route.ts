import { NextResponse } from "next/server";

import { visibleSchema } from "@/lib/schema";

export async function GET(request: Request) {
  const url = new URL(request.url);
  return NextResponse.json(visibleSchema(url.searchParams.get("userId") || undefined));
}
