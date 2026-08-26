// Wrangler cannot discover Secrets because their values must never be committed.
// This augments the generated Env with the names provisioned by `wrangler secret put`.
interface Env {
  LOSTARK_API_TOKEN: string;
  TURNSTILE_SECRET?: string;
}
