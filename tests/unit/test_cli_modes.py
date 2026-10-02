from steg.cli import main


def test_cli_executes_historical_mode_file(tmp_path, capsys):
    method = tmp_path / "padiel.yaml"
    method.write_text(
        """
id: padiel
mode:
  name: Padiel
  family: block_word_initials
  historical_notation: ".o"
  parameters:
    idle_run: 1
    significant_run: 1
    starts_with: significant
""".strip(),
        encoding="utf-8",
    )
    rc = main([str(method), "--text", "Alpha beta Gamma delta"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "AG"


def test_cli_rejects_unbound_stateful_mode(tmp_path, capsys):
    method = tmp_path / "stateful.yaml"
    method.write_text(
        """
id: stateful
mode:
  name: Stateful
  family: block_word_initials
  historical_notation: "o.."
  parameters:
    idle_run: 1
    significant_run: 2
    starts_with: idle
  modifiers:
    - type: boundary_reset
""".strip(),
        encoding="utf-8",
    )
    rc = main([str(method), "--text", "a b c d"])
    assert rc == 2
    assert "case parameter" in capsys.readouterr().err
