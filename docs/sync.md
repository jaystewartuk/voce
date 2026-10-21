# Pick up on another device

```sh
voce --sync you/voce
```

makes a private repository on GitHub (with `gh`, if it is signed in; or give any git URL), and keeps your
places, settings and a prepared copy of every document in your playlist there. From then on voce pulls when it
starts and pushes when you stop, so a second computer carries on where the first left off. `voce --sync` on its own
prepares and pushes the playlist again.

A prepared copy (`prepared/<hash>.json`) is the document as voce shows and says it: the blocks, and each
sentence or line of code as words. Another device needs only that and a voice; it does none of the reading work.
Everything you open in the reader gets one. `prepared/index.json` lists them in playlist order.

The repository is yours, on any git host. There is no voce service, and nothing is sent anywhere else.

## On your phone, or any browser

[jaystewartuk.github.io/voce/app](https://jaystewartuk.github.io/voce/app/) is the same library in a web page.
Sign in with GitHub, choose the repository `voce --sync` made, and the page reads it through GitHub's API, plays
each document with a voice in the page, and writes your place back. It is static files on GitHub Pages. Add it to
the home screen and it opens like an app.

The page can also read for itself. voce's own reading code runs in the browser (Python compiled to WebAssembly,
loaded once), so in settings you can point it at a playlist README in any repository voce can reach, such as a
folder of notes, and it reads the files straight from there with nothing prepared on a computer first. "Open a
Markdown file" reads a file from the device the same way. Places are kept by the text's hash, so the computer and
the phone agree on where you are whichever one did the reading.

Two voices: the device's own, instantly, or Kokoro, the open voice model, which the browser downloads once
(about 90 MB, 330 MB with WebGPU) and runs on the device. Nothing is sent anywhere but GitHub. Signing in goes
through the voce GitHub App, which can reach only the repositories you install it on, and a tiny relay
([relay/](../relay/)) that swaps GitHub's sign-in code for a token and keeps nothing; the library never passes
through it. The token stays in that browser; disconnecting in settings forgets it, and removing the app on GitHub
signs out every device. A fine-grained token for the one repository can be pasted instead.
