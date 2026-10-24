"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_V2_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class TestPrompts:

    @pytest.fixture(autouse=True)
    def setup(self):
        """Carrega o prompt v2 uma vez para todos os testes da classe."""
        data = load_prompts(PROMPT_V2_PATH)
        assert data is not None, f"Não foi possível carregar {PROMPT_V2_PATH}"
        assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada no YAML"
        self.prompt = data[PROMPT_KEY]

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in self.prompt, "Campo 'system_prompt' não encontrado"
        system_prompt = (self.prompt.get("system_prompt") or "").strip()
        assert system_prompt != "", "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = (self.prompt.get("system_prompt") or "").lower()
        role_markers = ["você é", "voce e", "you are", "atue como", "na posição de", "na posicao de"]
        assert any(marker in system_prompt for marker in role_markers), (
            "Nenhuma definição de persona/papel encontrada no system_prompt "
            "(esperado algo como 'Você é um Product Manager...')"
        )

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        full_text = (
            (self.prompt.get("system_prompt") or "") + " " + (self.prompt.get("user_prompt") or "")
        ).lower()
        format_markers = ["markdown", "como um", "eu quero", "para que", "user story", "critérios de aceitação", "criterios de aceitacao"]
        assert any(marker in full_text for marker in format_markers), (
            "O prompt não menciona formato Markdown nem o padrão de User Story "
            "('Como um... Eu quero... Para que...')"
        )

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = (self.prompt.get("system_prompt") or "").lower()
        few_shot_markers = ["exemplo", "example", "entrada:", "saída:", "saida:", "input:", "output:"]
        assert any(marker in system_prompt for marker in few_shot_markers), (
            "Nenhum exemplo de entrada/saída (Few-shot) encontrado no system_prompt"
        )
        techniques = [t.lower() for t in self.prompt.get("techniques_applied", [])]
        assert any("few-shot" in t or "few shot" in t for t in techniques), (
            "'few-shot' não está listado em techniques_applied"
        )

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        full_text = (self.prompt.get("system_prompt") or "") + (self.prompt.get("user_prompt") or "")
        assert "[TODO]" not in full_text, "Ainda há um [TODO] pendente no prompt"

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = self.prompt.get("techniques_applied", [])
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas em 'techniques_applied', encontradas: {len(techniques)}"
        )

    def test_prompt_structure_is_valid(self):
        """Teste extra: reaproveita o validador oficial de utils.py."""
        is_valid, errors = validate_prompt_structure(self.prompt)
        assert is_valid, f"Prompt inválido: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
