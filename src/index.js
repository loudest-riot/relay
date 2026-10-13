// Loudest Riot Sounds / Relay — consent-first Resend signup endpoint.
// Keep RESEND_API_KEY in Cloudflare Workers Secrets, never in this repository.
const SEGMENT_ID = "f1b393b0-09cc-414d-b108-1158bbee75db";
const TOPIC_ID = "71a4080b-01fc-4cda-91f6-399e64576650";
const MAX_TOKEN_AGE_MS = 48 * 60 * 60 * 1000;
const encoder = new TextEncoder();

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer"
    }
  });
}
function htmlPage(title, content, status = 200) {
  const safe = String(content).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  return new Response('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>' + title + ' | Loudest Riot Sounds</title><style>body{margin:0;background:#071428;color:#e9f3ff;font:16px/1.7 system-ui,sans-serif;padding:clamp(28px,8vw,90px)}main{max-width:550px;margin:auto}a{color:#89c8ff}h1{font-size:clamp(32px,7vw,54px);line-height:1.1}</style><main><p>LOUDEST RIOT SOUNDS / SIGNALS</p><h1>' + title + '</h1><p>' + safe + '</p><p><a href="/">Return to Relay &rarr;</a></p></main>', {
    status,
    headers: {"content-type":"text/html; charset=utf-8","cache-control":"no-store","referrer-policy":"no-referrer","x-content-type-options":"nosniff"}
  });
}
function normalizeEmail(value) {
  if (typeof value !== "string") return "";
  const email = value.trim().toLowerCase();
  if (email.length > 254 || /[\s|<>]/.test(email) || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "";
  return email;
}
function keyFor(secret) {
  return crypto.subtle.importKey("raw", encoder.encode(secret), {name: "HMAC", hash: "SHA-256"}, false, ["sign", "verify"]);
}
function bytesToB64Url(bytes) {
  let str = "";
  for (const byte of bytes) str += String.fromCharCode(byte);
  return btoa(str).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}
function b64UrlToBytes(str) {
  const b64 = str.replaceAll("-", "+").replaceAll("_", "/");
  const binary = atob(b64.padEnd(Math.ceil(b64.length / 4) * 4, "="));
  return Uint8Array.from(binary, char => char.charCodeAt(0));
}
async function createToken(email, secret) {
  const data = email + "|" + String(Date.now());
  const key = await keyFor(secret);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", key, encoder.encode(data)));
  return bytesToB64Url(encoder.encode(data + "|" + bytesToB64Url(sig)));
}
async function parseToken(token, secret) {
  if (!token || token.length > 1100) return null;
  try {
    const parts = new TextDecoder().decode(b64UrlToBytes(token)).split("|");
    if (parts.length !== 3) return null;
    const [email, time, signature] = parts;
    const issuedAt = Number(time);
    if (!normalizeEmail(email) || !Number.isSafeInteger(issuedAt) ||
        issuedAt > Date.now() + 120000 || Date.now() - issuedAt > MAX_TOKEN_AGE_MS) return null;
    const key = await keyFor(secret);
    const valid = await crypto.subtle.verify("HMAC", key, b64UrlToBytes(signature), encoder.encode(email + "|" + time));
    return valid ? email : null;
  } catch (_) { return null; }
}
async function resend(env, path, method, body) {
  const response = await fetch("https://api.resend.com" + path, {
    method,
    headers: {
      "authorization": "Bearer " + env.RESEND_API_KEY,
      "content-type": "application/json"
    },
    ...(body === undefined ? {} : {body: JSON.stringify(body)})
  });
  const data = await response.json().catch(() => ({}));
  return {status: response.status, ok: response.ok, data};
}
async function requestConfirmation(request, env) {
  if (!env.RESEND_API_KEY) return json({ok:false,message:"Mailing list setup is in progress. Please check back soon."}, 503);
  if (request.headers.get("origin") !== new URL(request.url).origin) {
    return json({ok:false,message:"Please use the signup form on Relay."}, 403);
  }
  if (!(request.headers.get("content-type") || "").startsWith("application/json")) {
    return json({ok:false,message:"Expected JSON."}, 415);
  }
  if (Number(request.headers.get("content-length") || 0) > 2048) {
    return json({ok:false,message:"Request too large."}, 413);
  }
  let body;
  try {
    const raw = await request.text();
    if (raw.length > 2048) return json({ok:false,message:"Request too large."}, 413);
    body = JSON.parse(raw);
  } catch (_) { return json({ok:false,message:"Invalid submission."}, 400); }
  // Harmless-looking success for basic spambots that fill the hidden field.
  if (body.website) return json({ok:true,message:"Check your inbox for the confirmation link."});
  const email = normalizeEmail(body.email);
  if (!email || body.consent !== true) return json({ok:false,message:"Enter a valid email and check the consent box."}, 400);
  const token = await createToken(email, env.RESEND_API_KEY);
  const url = new URL(request.url);
  const confirm = url.origin + "/api/confirm?token=" + encodeURIComponent(token);
  const from = env.SIGNAL_FROM_EMAIL || "Loudest Riot Sounds <signals@drift.loudestriot.com>";
  const message = {
    from, to: [email], reply_to: "sounds@loudestriot.com",
    subject: "Confirm your place on the Loudest Riot signal list",
    text: "You requested Loudest Riot Sounds updates from Relay.\n\nConfirm your email here (valid for 48 hours):\n" + confirm + "\n\nIf this wasn't you, ignore this email. You will not be subscribed.",
    html: '<div style="background:#071428;color:#e9f3ff;padding:34px;font-family:Arial,sans-serif"><div style="max-width:520px;margin:auto"><p style="color:#9bcaff;font-size:12px;letter-spacing:.12em">LOUDEST RIOT SOUNDS / SIGNALS</p><h1 style="font-size:34px;line-height:1.05">Confirm your signal.</h1><p>You asked for updates about nøfuture releases, artwork, and transmissions from the field.</p><p><a href="' + confirm + '" style="display:inline-block;background:#83bcff;color:#061327;padding:14px 20px;text-decoration:none;font-weight:700">CONFIRM SUBSCRIPTION</a></p><p style="color:#abbdd7;font-size:13px">Link expires in 48 hours. Ignore this message if you did not request it.</p></div></div>'
  };
  const result = await resend(env, "/emails", "POST", message);
  if (!result.ok) {
    console.error("Resend confirmation failed", result.status, result.data?.name || "");
    return json({ok:false,message:"Could not send a confirmation right now. Please try again later."}, 502);
  }
  return json({ok:true,message:"Check your inbox for a confirmation link. You're not subscribed until you click it."});
}
async function confirmContact(request, env) {
  if (!env.RESEND_API_KEY) return htmlPage("Not available", "Mailing-list configuration is not complete yet.", 503);
  const token = new URL(request.url).searchParams.get("token");
  const email = await parseToken(token, env.RESEND_API_KEY);
  if (!email) return htmlPage("Link expired", "This confirmation link has expired or is invalid. Please request a new one from Relay.", 400);
  try {
    const record = await resend(env, "/contacts/" + encodeURIComponent(email), "GET");
    if (record.ok) {
      if (record.data.unsubscribed === true) {
        return htmlPage("Subscription paused", "This address has an existing unsubscribe preference. Contact the label if you'd like help reviewing it.");
      }
      const topic = await resend(env, "/contacts/" + encodeURIComponent(email) + "/topics", "PATCH", [
        {id: TOPIC_ID, subscription: "opt_in"}
      ]);
      const group = await resend(env, "/contacts/" + encodeURIComponent(email) + "/segments/" + SEGMENT_ID, "POST");
      if (!topic.ok || !(group.ok || group.status === 409)) {
        console.error("Resend existing contact update failure", topic.status, group.status);
        return htmlPage("Try again", "We couldn't finish your subscription. Please try the confirmation link again.", 502);
      }
    } else if (record.status === 404) {
      const newContact = await resend(env, "/contacts", "POST", {
        email, unsubscribed: false,
        segments: [{id: SEGMENT_ID}],
        topics: [{id: TOPIC_ID, subscription: "opt_in"}]
      });
      if (!newContact.ok) {
        console.error("Resend contact creation failure", newContact.status);
        return htmlPage("Try again", "We couldn't finish your subscription. Please try the confirmation link again.", 502);
      }
    } else {
      console.error("Resend contact lookup failure", record.status);
      return htmlPage("Try again", "We couldn't verify your subscription right now. Please try again shortly.", 502);
    }
    return htmlPage("Signal confirmed", "You're subscribed to Loudest Riot Sounds updates. New sounds, cover art, and field transmissions are headed your way.");
  } catch (error) {
    console.error("Confirmation error", String(error));
    return htmlPage("Try again", "The confirmation service is temporarily unavailable. Please try again later.", 503);
  }
}
export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (path === "/api/signup-status" && request.method === "GET") {
      return json({ready: Boolean(env.RESEND_API_KEY)});
    }
    if (path === "/api/subscribe") {
      if (request.method !== "POST") return json({ok:false,message:"Method not allowed."}, 405);
      try { return await requestConfirmation(request, env); }
      catch (error) {
        console.error("Signup error", String(error));
        return json({ok:false,message:"The signup service is unavailable. Please try again later."}, 503);
      }
    }
    if (path === "/api/confirm") {
      if (request.method !== "GET") return json({ok:false,message:"Method not allowed."}, 405);
      return confirmContact(request, env);
    }
    if (path.startsWith("/api/")) return json({ok:false,message:"Not found."}, 404);
    return env.ASSETS.fetch(request);
  }
};
