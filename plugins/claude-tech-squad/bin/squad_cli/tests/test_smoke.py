def test_import_cli():
    from squad_cli import cli
    assert hasattr(cli, "main")
