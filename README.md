# Relay Network · nøfuture

Static source for the Hines Park Relay site at **relay.loudestriot.com**.

## Site

- Navy and cobalt-blue palette with cool pale text.
- Image-filled RELAY NETWORK lettering: the artwork shows through the title.
- Six existing compositions, plus current artwork previews for Newburgh Afterimage, Outre Drive, and SLY PILOT.
- New cover previews are *not* described as released music or linked to invented listening URLs.
- iPhone-friendly responsive layout, tap-to-expand artwork, keyboard focus, and reduced-motion support.
- Official brand imagery and Signal Glyph link to go.loudestriot.com.

## Cloudflare Workers Git deployment

This repository is connected to the **relay** Cloudflare Worker with production branch `main`.

- Build command: **leave blank**. There is no framework or compilation.
- Deploy command: `npx wrangler deploy` (the Cloudflare default).
- Root directory: repository root.
- `wrangler.jsonc` instructs Cloudflare to serve the static site directly from this repository.
- `.assetsignore` prevents publishing repository metadata as web assets.
- `_redirects` keeps the four legacy Ditto listening routes. Verify those destinations periodically.

Any push to `main` should trigger a Cloudflare Worker build and deployment. See the Cloudflare **Deployments** tab for its status. A commit alone does not prove that a deployment succeeded.

If the Worker doesn't yet own `relay.loudestriot.com`, add the domain under **Worker > Settings > Domains & Routes** after verifying the workers.dev preview. Avoid removing a previously live route before confirming the replacement.

## Contents

- `index.html`: responsive single-page gallery and artwork viewer.
- `assets/`: artwork, hero image, official logos, and Signal Glyph.
- `_redirects`: legacy listening links.
- `wrangler.jsonc`: Workers static-assets configuration.

Updated 12 October 2026.

## Mailing-list signup

`JOIN THE SIGNAL` uses a Cloudflare Worker API and the dedicated Resend subscriber segment. Set the Worker secret `RESEND_API_KEY` through Cloudflare's dashboard. Do not commit the API key or paste it into a webpage. The form deliberately stays disabled until the secret exists.

Confirmations use `signals@drift.loudestriot.com` while the main sending domain is being verified. Once `loudestriot.com` is verified in Resend, set Worker variable `SIGNAL_FROM_EMAIL` to `Loudest Riot Sounds <sounds@loudestriot.com>`.

Verify `loudestriot.com` in Resend after adding the DKIM and SPF records shown in the Resend domain settings. Review anti-abuse protections and test one consent-based signup before sharing the link publicly.
