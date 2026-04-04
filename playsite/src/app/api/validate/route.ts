import { NextRequest, NextResponse } from "next/server";
import { saveCommand } from "../../lib/db/storage";

const PYTHON_AI_URL = process.env.PYTHON_AI_URL || "http://localhost:5001";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { command, sessionId } = body;

    if (!command || typeof command !== "string") {
      return NextResponse.json({ error: "Invalid command" }, { status: 400 });
    }

    const trimmed = command.trim();
    if (!trimmed) {
      return NextResponse.json({ error: "Empty command" }, { status: 400 });
    }

    // Call local Python AI service
    const aiResponse = await fetch(`${PYTHON_AI_URL}/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: trimmed }),
    });

    if (!aiResponse.ok) {
      const errText = await aiResponse.text();
      throw new Error(`AI service error: ${errText}`);
    }

    const result = await aiResponse.json();

    // Persist to storage
    if (sessionId) {
      await saveCommand(sessionId, trimmed, result);
    }

    return NextResponse.json(result);
  } catch (err: any) {
    console.error("Validate route error:", err);
    return NextResponse.json(
      { error: err.message || "Validation failed" },
      { status: 500 }
    );
  }
}
