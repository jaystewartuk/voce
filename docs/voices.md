# Voices

voce has six voice engines. One runs on your Mac and is the default; the rest are cloud services used when their
key is set.

| Engine | Runs | Set up with | Free each month, when this was written |
| --- | --- | --- | --- |
| Kokoro | on your Mac | nothing: it is installed with voce | everything |
| Mac | on your Mac | nothing | everything |
| Google Chirp 3 HD | Google Cloud | `VOCE_GOOGLE_API_KEY`, or gcloud (see below) | 1,000,000 characters, about 18 hours |
| Azure | Microsoft Azure | `VOCE_AZURE_KEY` and `VOCE_AZURE_REGION` | 500,000 characters |
| ElevenLabs | ElevenLabs | `VOCE_ELEVENLABS_API_KEY` | 10,000 characters |
| OpenAI | OpenAI | `VOCE_OPENAI_API_KEY` | nothing |

`voce --voices` shows which are set up, which is in use, each one's voices and this month's count.

## Which one is used

The engine you chose last time, with `--engine`, `--voice` or the V key. Before you have chosen, the first cloud
engine that is set up, in the order of the table; and when none is, Kokoro. The Mac's voices are used when Kokoro
can't run (Python 3.9), when its model can't be downloaded, and when the Mac is the only thing left.

When an engine fails on a sentence, voce reads that sentence with Kokoro (or the Mac) and shows the reason in the
status bar. After three failures in a row it rests the engine for a minute, then tries again.

## Choosing a voice

Press <kbd>v</kbd> while listening to move through the engine's voices, and <kbd>V</kbd> to move to the next
engine. Both are remembered, and so is the voice you reached on each engine.

Or name a voice. The engine follows from the name when the name can only be one engine's:

```bash
voce --voice bm_george notes.md            # Kokoro: a letter for the language, f or m, an underscore, a name
voce --voice en-GB-Chirp3-HD-Leda notes.md # Google: any voice on its supported voices page
voce --voice en-GB-RyanNeural notes.md     # Azure: any voice in its gallery
voce --voice ash notes.md                  # OpenAI: alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse
voce --engine elevenlabs --voice Alice     # ElevenLabs: a premade voice's name, one of your own, or a voice ID
voce --mac --voice Daniel                  # the Mac: anything say -v ? lists
```

A plain word such as `Daniel` is a Mac voice, unless ElevenLabs is the engine in use.

## Kokoro

Kokoro is an 82-million-parameter open voice model (Apache 2.0), run here with `kokoro-onnx`. The first time it
speaks, voce downloads the model and its voices (120 MB) from the kokoro-onnx releases on GitHub into
`~/.cache/voce/kokoro`, and says so. That is the only thing Kokoro ever fetches. A sentence takes about a quarter
of its length to make on an Apple silicon Mac, and voce makes eight sentences ahead, so it keeps up.

The v key goes through eight voices: Heart, Bella, Michael, Fenrir and Nicole are American, and Emma, George and
Fable are British. The model has 54 in all, across nine languages; `--voice` takes any of their names.

## Google

You need a Google Cloud project with the Text-to-Speech API turned on, and one way to sign in.

1. Create a project in the [Google Cloud console](https://console.cloud.google.com/projectcreate), or pick one
   you already have. Billing has to be enabled on it, even if you stay inside the free tier.
2. Turn on the [Cloud Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)
   for that project.
3. Either make an API key under [APIs & Services, Credentials](https://console.cloud.google.com/apis/credentials),
   restrict it to the Text-to-Speech API, and export it from your shell profile:
   ```bash
   export VOCE_GOOGLE_API_KEY=your-key
   ```
   Or, if you use the [gcloud CLI](https://cloud.google.com/sdk/docs/install):
   ```bash
   gcloud auth login
   voce --google-project your-project-id   # saved, so you only do this once
   ```
   voce asks gcloud for a fresh access token every 45 minutes and bills the project you named. You can set
   `VOCE_GOOGLE_PROJECT` instead; if neither is set, voce uses `gcloud config get-value project`.

voce sends the key only to `texttospeech.googleapis.com` and never writes it to disk. The v key goes through
eight Chirp 3 HD voices, staying in the language of the current one; any voice on Google's
[supported voices page](https://cloud.google.com/text-to-speech/docs/chirp3-hd) works with `--voice`.

| Message | Fix |
| --- | --- |
| `403 ... has not been used in project` | Turn on the Text-to-Speech API for the project. |
| `403 ... requires a quota project` | Run `voce --google-project your-project-id`. |
| `400 ... API key not valid` | Check `VOCE_GOOGLE_API_KEY`, and that the key allows Text-to-Speech. |
| `gcloud ... returned non-zero exit status` | Run `gcloud auth login` again. |

## Azure

Create a Speech resource in the [Azure portal](https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices)
and copy one of its keys and its region:

```bash
export VOCE_AZURE_KEY=your-key
export VOCE_AZURE_REGION=uksouth
```

`AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` work too. The v key goes through Ava, Andrew, Emma and Brian
(American, multilingual) and Sonia, Ryan, Libby and Ollie (British); any voice in the
[voice gallery](https://speech.microsoft.com/portal/voicegallery) works with `--voice`. Azure reads every word as
written, and its free tier is 500,000 neural characters a month.

## ElevenLabs

Make an API key in your [ElevenLabs profile](https://elevenlabs.io/app/settings/api-keys):

```bash
export VOCE_ELEVENLABS_API_KEY=your-key
```

`ELEVENLABS_API_KEY` works too. The v key goes through George, Sarah, Brian, Alice, Daniel, Matilda, Liam and
Lily. `--voice` takes any premade voice's name, the name of a voice in your own library, or a voice ID. The model
is `eleven_multilingual_v2`; set `VOCE_ELEVENLABS_MODEL` to use another, such as `eleven_flash_v2_5`. The free
tier is small, 10,000 characters a month, and the paid tiers are the dearest of the four.

## OpenAI

Make an API key on the [OpenAI platform](https://platform.openai.com/api-keys):

```bash
export VOCE_OPENAI_API_KEY=your-key
```

`OPENAI_API_KEY` works too. The model is `gpt-4o-mini-tts`, told to read every word as written at a steady pace;
set `VOCE_OPENAI_TTS_MODEL` to use `tts-1` or `tts-1-hd` instead. The v key goes through all eleven voices.
There is no free tier, but it is the cheapest of the cloud engines per hour of listening.

## What it costs

Each sentence is sent once per voice. The audio is cached in `~/.cache/voce`, so listening again, going back, or
re-reading a file you have edited costs nothing for the sentences that didn't change. voce counts the characters
sent to each cloud engine each month and shows the count in the playlist menu, in `voce --list`, in `voce --voices`
and when you quit. `--prepare` and `--export` warn before taking a month past an engine's free amount. Check
each service's pricing page for current figures; the free amounts above were right when this was written.

To use the Mac's voices for one session, run `voce --mac`. To stop a cloud engine for good, unset its key.
