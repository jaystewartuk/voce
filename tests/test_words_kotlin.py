from __future__ import annotations

import pytest

from voce.speech import spoken_line
from voce.speech.words import KOTLIN, language


def test_fence_names_and_file_extensions_mean_kotlin():
    assert language("kotlin") is KOTLIN
    assert language("kt") is KOTLIN
    assert language("kts") is KOTLIN


@pytest.mark.parametrize(("line", "spoken"), [
    # Null safety, by the docs' names.
    ("val l = b?.length ?: 0", "val l equals b safe call length elvis 0"),
    ("val y = x?.let { it + 1 } ?: return", "val y equals x safe call let it plus 1 elvis return"),
    ("var name: String? = null", "var name colon String nullable equals null"),
    # Referential and structural equality.
    ("if (a === b) return", "if a is referentially equal to b return"),
    ("if (a !== b) return", "if a is not referentially equal to b return"),
    ("if (b == 0) a else b", "if b is equal to 0 a else b"),
    # % is rem, and the bitwise infix functions are said in full.
    ("tailrec fun gcd(a: Int, b: Int): Int = if (b == 0) a else gcd(b, a % b)",
     "tail rec fun gcd a colon Int, b colon Int colon Int equals if b is equal to 0 a else gcd b, a remainder b"),
    ("x %= 3", "x remainder equals 3"),
    ("val flags = mask shl 2 xor bits", "val flags equals mask shift left 2 X or bits"),
    ("if (x !in range) return", "if x not in range return"),
    # Keywords said as their words.
    ("lateinit var adapter: RecyclerAdapter", "late init var adapter colon Recycler Adapter"),
    ("fun sum(vararg numbers: Int): Int = numbers.sum()",
     "fun sum var arg numbers colon Int colon Int equals numbers dot sum"),
    ("inline fun run(noinline f: () -> Unit, crossinline g: () -> Unit) {}",
     "inline fun run no inline f colon arrow Unit, cross inline g colon arrow Unit"),
    ("typealias Handler = (String) -> Unit", "type alias Handler equals String arrow Unit"),
    ("data class User(val id: Long, val name: String)", "data class User val I D colon Long, val name colon String"),
    ("companion object { const val TAG = \"Main\" }", "companion object const val TAG equals Main"),
    # The standard library and the names around it.
    ("println(readln())", "print line read line"),
    ("val names = listOf(\"a\", \"b\").map { it.uppercase() }",
     "val names equals list Of a, b dot map it dot uppercase"),
    ("@JvmStatic fun main(args: Array<String>) {}",
     "at J V M Static fun main args colon Array of String"),
    ("val client = OkHttpClient.Builder().build()", "val client equals Ok H T T P Client dot Builder dot build"),
    ("val bytes = text.encodeUtf8()", "val bytes equals text dot encode U T F 8"),
    ("import kotlinx.coroutines.launch", "import kotlin X dot coroutines dot launch"),
    # Lambdas, when branches, labels, references and string templates.
    ("when (x) { 1 -> \"one\" else -> \"many\" }", "when x 1 arrow one else arrow many"),
    ("numbers.forEach { if (it == 0) return@forEach }", "numbers dot for Each if it is equal to 0 return at for Each"),
    ("val kClass = String::class", "val k Class equals String double colon class"),
    ("val greeting = \"Hello, $name\"", "val greeting equals Hello, name"),
])
def test_kotlin_lines(line, spoken):
    assert spoken_line(line, "kotlin") == spoken


@pytest.mark.parametrize(("line", "spoken"), [
    pytest.param("val l = b!!.length", "val l equals b not null assertion dot length"),
    pytest.param("for (i in 1..10) println(i)", "for i in 1 range to 10 print line i"),
    pytest.param("for (i in 0..<n step 2) print(i)", "for i in 0 range until n step 2 print i"),
    pytest.param("if (other !is Pin) return false", "if other is not Pin return false"),
    pytest.param("val a: String? = b as? String", "val a colon String nullable equals b safe cast to String",
                 marks=pytest.mark.xfail(reason="needs tokeniser: as? as one operator", strict=True)),
    pytest.param("println(\"Total: ${order.total}\")", "print line Total: order dot total"),
])
def test_kotlin_lines_that_need_the_tokeniser(line, spoken):
    assert spoken_line(line, "kotlin") == spoken
