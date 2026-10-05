# YouTube setup (one-time per channel, done by you)

This project runs one YouTube channel per narration language (e.g. `hi-en` for Hinglish,
`en` for English). Each channel needs its own Google Cloud OAuth client and its own
authorized token — repeat this whole guide once per channel. These steps need your own
Google account and a real browser, so I can't do them for you.

## 1. Create the channel
If you don't already have a channel for this language, create one at
https://www.youtube.com/create_channel. You can create multiple channels under the same
Google account as separate "Brand Accounts" — you'll pick which one to authorize in step 5.

## 2. Create a Google Cloud project + enable the API
You can reuse the **same** Google Cloud project for every channel — the project just needs
the YouTube Data API v3 enabled once.
1. Go to https://console.cloud.google.com/ and create a project (or reuse one from a
   previous channel setup).
2. **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**.

## 3. Configure the OAuth consent screen
Also reusable across channels — the consent screen belongs to the Cloud project, not to a
specific YouTube channel.
1. **APIs & Services → OAuth consent screen** → User type **External**.
2. Fill in the required app name/support email fields.
3. Under **Test users**, add your own Google account's email.
4. Save. Leave the app in **Testing** status (see the gotcha below).

## 4. Create OAuth credentials — once per channel
You can reuse one OAuth Client ID across channels too, **but** each channel needs its own
authorized `token.json`, so the simplest mental model is: one `client_secret.json` is fine
to share, just copy it into each channel's folder.
1. **APIs & Services → Credentials → Create Credentials → OAuth client ID** → **Desktop app**.
2. Download the JSON, save it as `client_secret.json` under **each** channel's credentials
   folder in this project:
   - `physics-math-youtube/credentials/hi-en/client_secret.json`
   - `physics-math-youtube/credentials/en/client_secret.json`
   (Same file content is fine in both places — it's gitignored either way.)

## 5. Run the auth flow — once per channel (on the Mac, not the headless server)
The auth flow opens a real browser to complete Google's consent screen, so run it on this Mac:

```
cd physics-math-youtube
source .venv/bin/activate
python main.py auth --channel hi-en
```

When the browser opens, **make sure you pick the Hinglish channel's Brand Account** on the
account-chooser screen before granting access. This saves
`credentials/hi-en/token.json`.

Repeat for the second channel:
```
python main.py auth --channel en
```
This time pick the English channel's Brand Account. This saves `credentials/en/token.json`.

Since the pipeline actually runs on the Linux server, copy both token files over:
```
scp credentials/hi-en/token.json physics-yt-server:~/projects/physics-math-youtube/credentials/hi-en/
scp credentials/en/token.json physics-yt-server:~/projects/physics-math-youtube/credentials/en/
```

## Gotcha: tokens expire every 7 days in "Testing" mode
While the OAuth consent screen stays in **Testing** publishing status, refresh tokens issued
to test users expire after 7 days — for **each** channel independently. That means roughly
once a week you'll need to re-run `python main.py auth --channel <channel>` for every channel
and `scp` the new token over again.

The alternative is submitting the app for Google's verification (requires a privacy policy,
a verified domain, and a review that can take weeks) — generally not worth it while this is
a small personal operation. The weekly re-auth per channel is the practical tradeoff for now.

## Publishing
`python main.py publish --latest` (or `--run-id <id>`) reads which channel a run belongs to
from its stored `language` and uploads to that channel automatically — you don't need to
specify the channel again at publish time.
