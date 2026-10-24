package com.mohamedrejeb.calf.navigation

fun main() {
    var checks = 0
    fun checkCase(name: String, f: () -> Unit) { f(); checks++; println("PASS $name") }
    fun throwsArgument(f: () -> Unit): Boolean = try { f(); false } catch (_: IllegalArgumentException) { true }

    checkCase("NAV typed argument with no default unexpectedly rejected") {
        check(throwsArgument { NavArgument.Builder().setType(AdaptiveNavType.IntType).build() })
    }
    checkCase("NAV nullable explicit null default unexpectedly rejected") {
        check(throwsArgument { NavArgument.Builder().setType(AdaptiveNavType.StringType).setIsNullable(true).setDefaultValue(null).build() })
    }
    checkCase("NAV mismatched default accepted until putDefaultValue ClassCastException") {
        val argument = NavArgument.Builder().setType(AdaptiveNavType.IntType).setDefaultValue("not-an-int").build()
        check(try { argument.putDefaultValue("n", AdaptiveBundle()); false } catch (_: ClassCastException) { true })
    }
    checkCase("NAV StringArray inference missing despite built-in StringArrayType") {
        check(throwsArgument { AdaptiveNavType.inferFromValueType(arrayOf("x")) })
        val b = AdaptiveBundle(); AdaptiveNavType.StringArrayType.put(b,"x", arrayOf("ok")); check(AdaptiveNavType.StringArrayType[b,"x"]!!.contentEquals(arrayOf("ok")))
    }
    checkCase("NAV generic bundle wrong type throws instead of documented null") {
        val b = AdaptiveBundle(); b.putInt("x", 3)
        check(try { val value: String? = b["x"]; value?.length; false } catch (_: ClassCastException) { true })
    }
    checkCase("NAV getString coerces non-string rather than default/null") {
        val b = AdaptiveBundle(); b.putInt("x",42); check(b.getString("x") == "42"); check(b.getString("x", "fallback") == "42")
    }
    checkCase("NAV generic putObject rejects supported Float direct setter") {
        val b=AdaptiveBundle(); b.putFloat("x",1.5f); check(b.getFloat("x") == 1.5f); check(throwsArgument { b.putObject("x",1.5f) })
    }
    checkCase("NAV StringType serializes URI delimiters unescaped") {
        check(AdaptiveNavType.StringType.serializeAsValue("a/b?x=1&n=2#frag") == "a/b?x=1&n=2#frag")
    }
    checkCase("NAV numeric/boolean/array parse positive control") {
        check(AdaptiveNavType.IntType.parseValue("0xff")==255)
        check(AdaptiveNavType.LongType.parseValue("0xffL")==255L)
        check(AdaptiveNavType.BoolType.parseValue("true"))
        check(throwsArgument { AdaptiveNavType.BoolType.parseValue("TRUE") })
        check(AdaptiveNavType.IntArrayType.parseValue("2", intArrayOf(1)).contentEquals(intArrayOf(1,2)))
    }
    checkCase("NAV verify rejects wrong runtime type and required explicit null") {
        val arg = NavArgument.Builder().setType(AdaptiveNavType.IntType).setDefaultValue(1).build()
        val b = AdaptiveBundle(); b.putString("n", "text"); check(!arg.verify("n", b)); b.putString("n",null); check(!arg.verify("n",b)); b.putInt("n",4); check(arg.verify("n",b))
    }
    println("All $checks baseline-behavior checks passed; defect-confirmation assertions, not correctness sign-off")
}
