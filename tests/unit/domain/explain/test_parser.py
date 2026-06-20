"""Unit tests for the AST Parser and Lexical Analyzer."""
from pyregex.domain.explain.lexer.scanner import Scanner as RegexScanner
from pyregex.domain.explain.parser.regex_parser import RegexParser
from pyregex.domain.explain.ast.nodes import (
    LiteralNode, CharClassNode, GroupNode, RootNode,
    AlternationNode, QuantifierNode, AnchorNode
)

def test_scanner_basic_tokens():
    """Verify scanner correctly tokenizes literal strings."""
    # It also outputs an EOF token at the end
    tokens = RegexScanner("abc").scan()
    assert len(tokens) == 4
    assert tokens[0].value == "a"
    assert tokens[1].value == "b"
    assert tokens[2].value == "c"
    assert tokens[3].type.name == "EOF"

def test_parser_concatenation():
    """Verify parser forms a RootNode with children for sequences."""
    ast = RegexParser("abc").parse()
    assert isinstance(ast, RootNode)
    assert len(ast.children) == 3
    for child in ast.children:
        assert isinstance(child, LiteralNode)

def test_parser_alternation():
    """Verify parser correctly creates Alternation nodes."""
    ast = RegexParser("a|b").parse()
    assert isinstance(ast, RootNode)
    assert len(ast.children) == 1
    alt = ast.children[0]
    assert isinstance(alt, AlternationNode)
    # The parser optimizations behavior:
    assert isinstance(alt.left, LiteralNode)
    assert alt.left.value == "a"
    assert isinstance(alt.right, GroupNode)
    assert alt.right.children[0].value == "b"

def test_parser_quantifier():
    """Verify parsing of + * ?"""
    # Note: RegexParser currently wraps the quantified node directly
    ast = RegexParser("a+").parse()
    quant = ast.children[0]
    assert isinstance(quant, QuantifierNode)
    assert quant.min_cnt == 1
    assert quant.max_cnt is None  # Infinity
    assert isinstance(quant.child, LiteralNode)
    assert quant.child.value == "a"

def test_parser_anchors():
    """Verify parsing of ^ and $ anchors."""
    ast = RegexParser("^xyz$").parse()
    assert isinstance(ast, RootNode)
    assert isinstance(ast.children[0], AnchorNode)
    assert ast.children[0].type_ == "^"
    assert isinstance(ast.children[-1], AnchorNode)
    assert ast.children[-1].type_ == "$"

def test_parser_character_class():
    """Verify parsing of character sets [a-z]."""
    ast = RegexParser("[0-9]").parse()
    set_node = ast.children[0]
    assert isinstance(set_node, CharClassNode)
    assert "0-9" in set_node.chars
