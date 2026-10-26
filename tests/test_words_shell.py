"""The shell's words and operator names, as the Bash manual names them."""

from __future__ import annotations

import pytest

from voce.speech import spoken_line


@pytest.mark.parametrize("line, spoken", [
    ("ls -la | grep foo | wc -l", "L S dash la pipe grep foo pipe W C dash l"),                    # Pipelines
    ("chmod +x script.sh && ./script.sh", "C H mod plus x script dot S H and then dot slash script dot S H"),
    ("[ -z \"$x\" ] || return 1", "dash z x or else return 1"),
    ("echo ok > out.txt", "echo ok to out dot txt"),
    ("echo ok >> out.txt", "echo ok appended to out dot txt"),
    ("sort < in.txt", "sort from in dot txt"),
    ("read -r line <<< \"$input\"", "read dash r line here string input"),
    ("cmd > /dev/null", "command to slash dev slash null"),
    ("rm -rf node_modules", "R M dash R F node modules"),
    ("git clone --depth 1 https://github.com/a/b.git",
     "git clone dash dash depth 1 https colon slash slash github dot com slash A slash b dot git"),
    ("du -sh * | sort -h", "D U dash S H asterisk pipe sort dash h"),
    ("x=${f%.txt}", "x equals f percent dot txt"),
    ("elif [ -d \"$dir\" ]; then", "else if dash d dir, then"),
    ("fi", "end if"),
    ("esac", "end case"),
    ("done", "done"),
    ("ln -s /usr/bin/node /usr/local/bin/node", "L N dash s slash user slash bin slash node slash user slash local "
                                                "slash bin slash node"),
    ("xargs -0 rm", "X args dash 0 R M"),
    ("nohup ./run &", "no hup dot slash run ampersand"),
    ("echo \"$PATH\" | tr ':' '\\n'", "echo PATH pipe T R a colon a new line"),
    ("tar -xzf a.tar.gz", "tar dash X Z F A dot tar dot gz"),
    ("while IFS= read -r l; do", "while I F S equals read dash r l, do"),
    ("readonly X=1", "read only X equals 1"),
    ("echo ${X:=y}", "echo X assign default y"),
    ("[ \"$a\" -eq 1 ] && [ -n \"$b\" ]; then", "A is equal to 1 and then dash n b, then"),
])
def test_shell_lines(line, spoken):
    assert spoken_line(line, "bash") == spoken


# A redirection that starts with a digit is read as a number first, so the tokeniser cannot take it whole yet.
@pytest.mark.xfail(reason="needs tokeniser: 2>&1", strict=True)
def test_duplicating_file_descriptors():
    assert spoken_line("cmd 2>&1", "bash") == "command standard error to standard output"


def test_here_document():
    assert spoken_line("cat <<EOF", "bash") == "cat here document EOF"


def test_standard_output_and_error():
    assert spoken_line("cmd &> log", "bash") == "command standard output and standard error to log"


def test_regex_match():
    assert spoken_line("[[ $a =~ b ]]", "bash") == "A matches b"


def test_numeric_tests():
    assert spoken_line("[ $a -ge 1 ]", "bash") == "A is greater than or equal to 1"


def test_special_parameters():
    assert spoken_line("echo $?", "bash") == "echo the exit status"
