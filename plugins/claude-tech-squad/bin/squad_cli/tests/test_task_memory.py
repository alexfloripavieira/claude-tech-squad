from squad_cli.task_memory import TaskMemory


def test_bootstrap_keys_default_to_none(tmp_path):
    tm = TaskMemory(repo_root=tmp_path)
    assert tm.get("test_infra_bootstrapped") is None
    assert tm.get("debt_acknowledged") is None


def test_set_and_get_bootstrap_state(tmp_path):
    tm = TaskMemory(repo_root=tmp_path)
    tm.set("test_infra_bootstrapped", True)
    assert tm.get("test_infra_bootstrapped") is True


def test_persistence_across_instances(tmp_path):
    TaskMemory(repo_root=tmp_path).set("test_infra_bootstrapped", True)
    assert TaskMemory(repo_root=tmp_path).get("test_infra_bootstrapped") is True
