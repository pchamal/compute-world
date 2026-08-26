// Cloudflare Pages Function: POST /api/subscribe
// No secrets in git. Persist via D1 (DB), then KV (SUBSCRIBERS), then SUBSCRIBE_WEBHOOK.
// If none is configured, return 200 with stored:"pending" — do not promise email.
// No public GET. Roster is not on a public URL.

const ALLOWED = new Set(["countries", "silicon", "inference", "neoclouds", "hyperscalers"]);

const CREATE_SUBSCRIBERS = `CREATE TABLE IF NOT EXISTS subscribers (
  email TEXT PRIMARY KEY,
  lists TEXT NOT NULL,
  ts TEXT NOT NULL
)`;

const UPSERT_SUBSCRIBER = `INSERT INTO subscribers (email, lists, ts) VALUES (?, ?, ?)
  ON CONFLICT(email) DO UPDATE SET lists = excluded.lists, ts = excluded.ts`;

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function validEmail(email) {
  if (typeof email !== "string") return false;
  const e = email.trim();
  if (e.length < 5 || e.length > 254) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);
}

export async function onRequestPost({ request, env }) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid json" }, 400);
  }

  const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
  const raw = Array.isArray(body.lists) ? body.lists : ["countries", "silicon"];
  const lists = [...new Set(raw.filter((x) => ALLOWED.has(x)))];

  if (!validEmail(email)) return json({ error: "invalid email" }, 400);
  if (!lists.length) return json({ error: "choose at least one list" }, 400);

  const payload = { email, lists, ts: new Date().toISOString() };

  if (env.DB) {
    await env.DB.prepare(CREATE_SUBSCRIBERS).run();
    await env.DB.prepare(UPSERT_SUBSCRIBER).bind(email, JSON.stringify(lists), payload.ts).run();
    return json({ ok: true, stored: "d1" }, 200);
  }

  if (env.SUBSCRIBERS) {
    await env.SUBSCRIBERS.put(email, JSON.stringify({ lists, ts: payload.ts }));
    return json({ ok: true, stored: "kv" }, 200);
  }

  if (env.SUBSCRIBE_WEBHOOK) {
    const r = await fetch(env.SUBSCRIBE_WEBHOOK, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) return json({ error: "webhook failed" }, 502);
    return json({ ok: true, stored: "webhook" }, 200);
  }

  console.log("subscribe pending", JSON.stringify(payload));
  return json({ ok: true, stored: "pending" }, 200);
}
