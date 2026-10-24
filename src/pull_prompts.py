"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

SEED_PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt semente (baixa qualidade) do LangSmith Prompt Hub
    e salva o resultado localmente em formato YAML.

    Returns:
        True se sucesso, False caso contrário
    """
    print(f"   Puxando prompt do LangSmith Hub: {SEED_PROMPT_NAME}")

    client = Client()

    try:
        prompt_template = client.pull_prompt(
            SEED_PROMPT_NAME,
            dangerously_pull_public_prompt=True,
        )
    except Exception as e:
        print(f"❌ Erro ao puxar o prompt '{SEED_PROMPT_NAME}': {e}")
        return False

    print("   ✓ Prompt carregado com sucesso")

    # Extrai system_prompt e user_prompt a partir das mensagens do
    # ChatPromptTemplate retornado pelo Hub.
    system_prompt = ""
    user_prompt = ""

    for message in prompt_template.messages:
        # Cada "message" é um *MessagePromptTemplate com um atributo
        # .prompt (ou lista de .prompt, no caso de mensagens compostas)
        # que expõe .template com o texto bruto.
        role = message.__class__.__name__.lower()
        template_text = getattr(message.prompt, "template", "")

        if "system" in role:
            system_prompt = template_text
        elif "human" in role or "user" in role:
            user_prompt = template_text

    prompt_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt para converter relatos de bugs em User Stories (baixa qualidade, puxado do LangSmith Hub)",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "source": SEED_PROMPT_NAME,
        }
    }

    success = save_yaml(prompt_data, OUTPUT_PATH)

    if success:
        print(f"   ✓ Prompt salvo em: {OUTPUT_PATH}")

    return success


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPT DO LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        return 1

    os.makedirs("prompts", exist_ok=True)

    success = pull_prompts_from_langsmith()

    if success:
        print("\n✅ Prompt v1 puxado e salvo com sucesso.")
        return 0
    else:
        print("\n❌ Falha ao puxar o prompt.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
