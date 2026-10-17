# Security

voce runs locally. It sends text only to Google's Text-to-Speech API, and only when Google voices are set up.

If you find a security problem, such as a way for a crafted Markdown file or transcript to run commands or read
files it shouldn't, please report it privately through
[GitHub's private vulnerability reporting](https://github.com/jaystewartuk/voce/security/advisories/new) rather
than in a public issue. You should hear back within a week.

Keep your `VOCE_GOOGLE_API_KEY` restricted to the Text-to-Speech API, as described in
[docs/google-voices.md](docs/google-voices.md).
