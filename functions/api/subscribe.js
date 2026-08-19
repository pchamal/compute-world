// Cloudflare Pages Function: POST /api/subscribe
// No secrets in git. Persist via SUBSCRIBE_WEBHOOK or KV binding SUBSCRIBERS.
// If neither is configured, return 200 with stored:"pending" — do not promise email.

const ALLOWED = new Set(["countries", "silicon", "inference", "neoclouds", "hyperscalers"]);

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

  if (env.SUBSCRIBE_WEBHOOK) {
    const r = await fetch(env.SUBSCRIBE_WEBHOOK, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) return json({ error: "webhook failed" }, 502);
    return json({ ok: true, stored: "webhook" }, 200);
  }

  if (env.SUBSCRIBERS) {
    await env.SUBSCRIBERS.put(email, JSON.stringify({ lists, ts: payload.ts }));
    return json({ ok: true, stored: "kv" }, 200);
  }

  console.log("subscribe pending", JSON.stringify(payload));
  return json({ ok: true, stored: "pending" }, 200);
}
