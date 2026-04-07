from pyregex.domain.explain.ast.nodes import (
    LiteralNode,
    AlternationNode,
    QuantifierNode,
    GroupNode,
    CharClassNode,
    AnchorNode,
    RootNode,
)

def test_literal_node():
    node = LiteralNode("a")
    assert node.value == "a"
    assert repr(node) == "Literal('a')"

def test_root_node():
    n1 = LiteralNode("a")
    n2 = LiteralNode("b")
    root = RootNode([n1, n2])
    assert len(root.children) == 2

def test_alternation_node():
    n1 = LiteralNode("a")
    n2 = LiteralNode("b")
    alt = AlternationNode(left=n1, right=n2)
    assert alt.left.value == "a"
    assert alt.right.value == "b"

def test_quantifier_node():
    child = LiteralNode("a")
    q1 = QuantifierNode(child, min_cnt=1, max_cnt=1, greedy=True)
    assert q1.greedy == True
    assert q1.min_cnt == 1
    
    q2 = QuantifierNode(child, min_cnt=0, max_cnt=None, greedy=False)
    assert getattr(q2, "greedy", False) == False
    assert q2.max_cnt is None

def test_group_node():
    child = LiteralNode("a")
    g = GroupNode([child], is_capture=True, name="mygroup")
    assert g.is_capture
    assert g.name == "mygroup"
    assert len(g.children) == 1

def test_charclass_node():
    cc = CharClassNode(chars="abc", negated=True)
    assert cc.negated
    assert cc.chars == "abc"
    assert repr(cc) == "CharClass([^abc])"

def test_anchor_node():
    a = AnchorNode(type_="^")
    assert a.type_ == "^"
    assert repr(a) == "Anchor('^')"
