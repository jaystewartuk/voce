# Run through docs/demo/record.sh, which sets VOCE_DEMO_HOME.
Output docs/assets/demo.gif

Set Shell zsh
Set FontSize 22
Set Width 1280
Set Height 720
Set Padding 26
Set Framerate 20
Set TypingSpeed 70ms
Set WindowBar Colorful
Set BorderRadius 10
Set Theme { "name": "voce", "black": "#1b1f27", "red": "#e5534b", "green": "#57ab5a", "yellow": "#c69026", "blue": "#2f6feb", "magenta": "#b083f0", "cyan": "#39c5cf", "white": "#c9d1d9", "brightBlack": "#6e7681", "brightRed": "#ff7b72", "brightGreen": "#7ee787", "brightYellow": "#e3b341", "brightBlue": "#6ca4f8", "brightMagenta": "#d2a8ff", "brightCyan": "#56d4dd", "brightWhite": "#f0f6fc", "background": "#0e1116", "foreground": "#e6edf3", "selection": "#264f78", "cursor": "#2f6feb" }

Hide
Type "export PATH=$PWD/.venv/bin:$PATH CLAUDE_CONFIG_DIR=$VOCE_DEMO_HOME/claude XDG_STATE_HOME=$VOCE_DEMO_HOME/state XDG_CACHE_HOME=$VOCE_DEMO_HOME/cache TERM=xterm-256color PROMPT='%F{39}❯%f '"
Enter
Type "voce() { command voce --mute $@ }; clear"
Enter
Sleep 1s
Show

Sleep 700ms
Type "voce -r"
Sleep 500ms
Enter
Sleep 11s
Screenshot docs/assets/screenshot.png
Sleep 4s
Down
Sleep 7s
Type "q"
Sleep 1500ms
