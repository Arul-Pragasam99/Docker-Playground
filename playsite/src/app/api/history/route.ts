import { NextRequest, NextResponse } from "next/server";
import { getHistory, clearHistory } from "@/lib/db/storage";

export async function GET(req: NextRequest) {
  const sessionId = req.nextUrl.searchParams.get("sessionId");
  if (!sessionId) {
    return NextResponse.json({ error: "sessionId required" }, { status: 400 });
  }
  const history = await getHistory(sessionId);
  return NextResponse.json({ history });
}

export async function DELETE(req: NextRequest) {
  const sessionId = req.nextUrl.searchParams.get("sessionId");
  if (!sessionId) {
    return NextResponse.json({ error: "sessionId required" }, { status: 400 });
  }
  await clearHistory(sessionId);
  return NextResponse.json({ ok: true });
}
