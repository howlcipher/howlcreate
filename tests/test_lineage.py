"""Tests for concept lineage graph and DAG invariants."""

from howlcreate.models.idea import Idea, LineageGraph


def test_lineage_graph_dag_integrity():
    graph = LineageGraph()

    # Create root
    root = Idea(id="root-1", title="Root Concept", description="Root idea")
    graph.add_idea(root)

    # Derive child 1
    child1 = Idea(id="child-1", title="Child 1", description="Child 1", parent_ids=["root-1"], operator_used="mutation")
    graph.add_idea(child1)

    # Derive child 2
    child2 = Idea(id="child-2", title="Child 2", description="Child 2", parent_ids=["root-1"], operator_used="analogy")
    graph.add_idea(child2)

    # Derive grandchild from child 1 and child 2 (forced combination)
    grandchild = Idea(
        id="grandchild-1",
        title="Grandchild Hybrid",
        description="Hybrid",
        parent_ids=["child-1", "child-2"],
        operator_used="forced_combination"
    )
    graph.add_idea(grandchild)

    # Validate DAG (must be acyclic)
    assert graph.validate_dag() is True

    # Test ancestors
    ancestors = graph.get_ancestors("grandchild-1")
    assert "child-1" in ancestors
    assert "child-2" in ancestors
    assert "root-1" in ancestors

    # Test descendants of root
    descendants = graph.get_descendants("root-1")
    assert "child-1" in descendants
    assert "child-2" in descendants
    assert "grandchild-1" in descendants


def test_lineage_cycle_detection():
    graph = LineageGraph()
    idea_a = Idea(id="a", title="Idea A", description="A")
    idea_b = Idea(id="b", title="Idea B", description="B", parent_ids=["a"])
    graph.add_idea(idea_a)
    graph.add_idea(idea_b)

    assert graph.validate_dag() is True

    # Artificially inject a cycle: b -> a
    graph.add_edge("b", "a", "invalid_loop")
    assert graph.validate_dag() is False


def test_lineage_graph_serialization():
    graph = LineageGraph()
    idea1 = Idea(id="i1", title="I1", description="Desc 1")
    idea2 = Idea(id="i2", title="I2", description="Desc 2", parent_ids=["i1"])
    graph.add_idea(idea1)
    graph.add_idea(idea2)

    data = graph.to_dict()
    restored = LineageGraph.from_dict(data)

    assert len(restored.nodes) == 2
    assert len(restored.edges) == 1
    assert restored.edges[0].parent_id == "i1"
    assert restored.edges[0].child_id == "i2"
