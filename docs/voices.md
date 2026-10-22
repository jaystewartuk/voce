# Voices

voce has two voice engines, and both run on your computer. Nothing you read is sent anywhere, and nothing costs
anything.

| Engine | Runs on | Set up with |
| --- | --- | --- |
| Kokoro | macOS and Linux, with Python 3.10 to 3.14 | nothing: it is installed with voce |
| Mac | macOS | nothing |

`voce --voices` shows which are set up, which is in use, and each one's voices.

## Which one is used

The engine you chose last time, with `--engine`, `--voice` or the V key. Before you have chosen, Kokoro. The
Mac's voices are used when Kokoro can't run (Python 3.9), when its model can't be downloaded, and as the backup.

When Kokoro fails on a sentence, voce reads that sentence with the Mac's voice and shows the reason in the status
bar. After three failures in a row it rests Kokoro for a minute, then tries again.

If you chose a cloud engine in an earlier version of voce (Google, Azure, ElevenLabs or OpenAI), voce now uses
Kokoro instead, with the Kokoro voice you used last.

## Choosing a voice

Press <kbd>v</kbd> while listening to move through the engine's voices, and <kbd>V</kbd> to move to the other
engine. Both are remembered, and so is the voice you reached on each engine.

Or name a voice, and the engine follows from the name:

```bash
voce --voice bm_george notes.md   # Kokoro: a letter for the language, f or m, an underscore, a name
voce --mac --voice Daniel         # the Mac: anything say -v ? lists
```

## Kokoro

Kokoro is an 82-million-parameter open voice model (Apache 2.0), run here with `kokoro-onnx`. The first time it
speaks, voce downloads the model and its voices (120 MB) from the kokoro-onnx releases on GitHub into
`~/.cache/voce/kokoro`, and says so. That is the only thing Kokoro ever fetches. A sentence takes about a quarter
of its length to make on an Apple silicon Mac, and voce makes eight sentences ahead, so it keeps up.

The v key goes through eight voices: Heart, Bella, Michael, Fenrir and Nicole are American, and Emma, George and
Fable are British. The model has 54 in all, across nine languages; `--voice` takes any of their names.

## The Mac's voices

`voce --mac` uses them for one session, and `voce --mac --voice Daniel` picks one. Add better ones in System
Settings, under Accessibility, Spoken Content, System voice, Manage voices.

Every sentence is made once per voice and kept in `~/.cache/voce`, so listening again, going back, or re-reading
a file you have edited is instant for the sentences that didn't change.
