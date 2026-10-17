# Google voices

voce uses Google Cloud's Text-to-Speech API for its Chirp 3 HD voices. You need a Google Cloud project with that
API turned on, and one way to sign in.

## 1. Make a project and turn on the API

1. Create a project in the [Google Cloud console](https://console.cloud.google.com/projectcreate), or pick one
   you already have. Billing has to be enabled on it, even if you stay inside the free tier.
2. Turn on the [Cloud Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)
   for that project.

## 2a. Sign in with an API key (simplest)

1. Create a key under [APIs & Services, Credentials](https://console.cloud.google.com/apis/credentials).
2. Restrict it to the Cloud Text-to-Speech API, so the key can do nothing else if it leaks.
3. Export it in your shell profile, for example `~/.zshrc`:

   ```bash
   export VOCE_GOOGLE_API_KEY=your-key
   ```

voce sends the key only to `texttospeech.googleapis.com`. It never writes it to disk.

## 2b. Or sign in with gcloud

If you already use the [gcloud CLI](https://cloud.google.com/sdk/docs/install):

```bash
gcloud auth login
voce --google-project your-project-id   # saved, so you only do this once
```

voce asks gcloud for a fresh access token every 45 minutes and bills the project you named. Instead of
`--google-project`, you can set `VOCE_GOOGLE_PROJECT`. If neither is set, voce uses
`gcloud config get-value project`.

## Choosing a voice

Press <kbd>v</kbd> while listening to move through eight Chirp 3 HD voices: Charon, Leda, Orus, Kore, Puck, Aoede,
Fenrir and Despina. voce stays in the language of the current voice and remembers your choice.

To use another language or a voice that isn't in the cycle, pass its full name once:

```bash
voce --voice en-GB-Chirp3-HD-Leda notes.md
voce --voice es-US-Chirp3-HD-Kore notas.md
```

Google lists every voice on its [supported voices page](https://cloud.google.com/text-to-speech/docs/chirp3-hd).

## What it costs

Each sentence is sent once per voice. The audio is cached in `~/.cache/voce`, so listening again, going back, or
re-reading a file you have edited costs nothing for the sentences that didn't change.

When this was written, the first million Chirp 3 HD characters each month were free. A million characters is
about 18 hours of listening at normal speed. voce counts the characters it sends each month. It shows the count
in the playlist menu, in `voce --list` and when you quit, and it warns before `--prepare` or `--export` would go
past the free amount. Check [Google's pricing page](https://cloud.google.com/text-to-speech/pricing) for current
figures, and set a [budget alert](https://cloud.google.com/billing/docs/how-to/budgets) if you want a hard stop.

## When something goes wrong

If a request fails, voce reads that sentence with the Mac voice and shows Google's error in the status bar. After
three failures in a row it stops trying Google until you start voce again. The usual causes are:

| Message | Fix |
| --- | --- |
| `403 ... has not been used in project` | Turn on the Text-to-Speech API for the project. |
| `403 ... requires a quota project` | Run `voce --google-project your-project-id`. |
| `400 ... API key not valid` | Check `VOCE_GOOGLE_API_KEY`, and that the key allows Text-to-Speech. |
| `gcloud ... returned non-zero exit status` | Run `gcloud auth login` again. |

To skip Google for one session, run `voce --mac`.
