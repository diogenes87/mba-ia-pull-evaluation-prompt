"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_YAML_PATH = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    client = Client()

    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt", "{bug_report}")

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt),
    ])

    techniques = prompt_data.get("techniques_applied", [])
    description = prompt_data.get(
        "description",
        "Prompt otimizado para converter relatos de bugs em User Stories",
    )

    tags = prompt_data.get("tags", []) + [f"technique:{t}" for t in techniques]

    try:
        url = client.push_prompt(
            prompt_name,
            object=chat_prompt,
            is_public=True,
            description=description,
            tags=tags,
        )
    except Exception as e:
        print(f"❌ Erro ao fazer push do prompt '{prompt_name}': {e}")
        return False

    print(f"   ✓ Push realizado com sucesso")
    print(f"   ✓ URL: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    return validate_prompt_structure(prompt_data)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPT OTIMIZADO PARA O LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB")

    all_prompts = load_yaml(PROMPT_YAML_PATH)
    if not all_prompts:
        print(f"❌ Não foi possível carregar {PROMPT_YAML_PATH}")
        return 1

    prompt_data = all_prompts.get(PROMPT_KEY)
    if not prompt_data:
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada em {PROMPT_YAML_PATH}")
        return 1

    print(f"Validando prompt '{PROMPT_KEY}'...")
    is_valid, errors = validate_prompt(prompt_data)

    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("   ✓ Prompt válido\n")

    prompt_name = f"{username}/{PROMPT_KEY}"
    print(f"Fazendo push de '{prompt_name}'...")

    success = push_prompt_to_langsmith(prompt_name, prompt_data)

    if success:
        print(f"\n✅ Prompt publicado com sucesso em: https://smith.langchain.com/prompts")
        print(f"   Nome: {prompt_name}")
        return 0
    else:
        print("\n❌ Falha ao publicar o prompt.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
