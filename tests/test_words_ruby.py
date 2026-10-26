from __future__ import annotations

import pytest

from voce.speech import spoken_line

# A line of Ruby and exactly how it should sound, with the operator names Ruby's own documentation uses.


@pytest.mark.parametrize("line, spoken", [
    ("attr_accessor :name, :email", "attribute accessor colon name, colon email"),
    ("cattr_accessor :logger", "class attribute accessor colon logger"),
    ("elsif count > 0", "else if count greater than 0"),
    # a block's parameters are said without their pipes
    ("items.each do |item|", "items dot each do item"),
    ("ary.each_with_index { |(k, v), i| puts k }", "array dot each with index k, v, i put S k"),
    ("h = { :foo => 0, :bar => 1 }", "h equals colon foo hash rocket 0, colon bar hash rocket 1"),
    ("result ||= compute(value)", "result or equals compute value"),
    ("by_size = a.size <=> b.size", "by size equals A dot size spaceship b dot size"),
    ("square = ->(x) { x * x }", "square equals lambda x x times x"),
    ("(0...n).map { |i| i * 2 }", "0 triple dot n dot map i i times 2"),
    ("Integer === value", "Integer case equals value"),
    ("mask = flags ^ mask_bits", "mask equals flags exclusive or mask bits"),
    ("half = size >> 1", "half equals size right shift 1"),
    ("$stdout.puts msg", "standard out dot put S message"),
    ("klass = Class.new(StandardError)", "class equals Class dot new Standard Error"),
    ("def initialize(name, **kwargs, &block)", "def initialize name, double star keyword args, ampersand block"),
    ("names.uniq.sort", "names dot unique dot sort"),
    ("rescue TZInfo::InvalidTimezoneIdentifier", "rescue T Z info double colon Invalid Timezone Identifier"),
    ("line.lstrip.rstrip.ljust(width)", "line dot L strip dot R strip dot L just width"),
    ("opts = attrs.dup", "options equals attributes dot dupe"),
    ("x = 1 # the first", "x equals 1, the first"),
])
def test_ruby_lines(line, spoken):
    assert spoken_line(line, "ruby") == spoken


def test_ruby_aliases():
    assert spoken_line("elsif ready", "rb") == "else if ready"
    assert spoken_line("elsif ready", "rake") == "else if ready"


# Operators, interpolation and method names that code.py takes whole for Ruby.
@pytest.mark.parametrize("line, spoken", [
    ("list << item", "list append item"),
    ("@expires_at = expires_at&.to_f || 0", "at expires at equals expires at safe navigation to f or 0"),
    ("return unless line =~ pattern", "return unless line matches pattern"),
    ("next if line !~ pattern", "next if line does not match pattern"),
    ("(1..10).each { |i| puts i }", "1 double dot 10 dot each i put S i"),
    ('puts "Hello #{name}"', "put S Hello name"),
    ("user.save!", "user dot save bang"),
    ("return if list.empty?", "return if list dot empty question mark"),
])
def test_ruby_operators_interpolation_and_method_names(line, spoken):
    assert spoken_line(line, "ruby") == spoken
