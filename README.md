# Godot SDD Template

Base reutilizável para Godot 4.7 com Spec Kit, papéis multiagente no Codex, testes gdUnit4 e ponte local MCP do Godot. O template não inclui conceito, mecânicas, assets ou aprovações de jogo.

## Requisitos

- Godot 4.7.x, com executável de linha de comando no PATH ou definido em GODOT_BIN
- Python 3.11+
- Node.js 20+ e npm
- Git
- Git Bash no Windows para os scripts shell oficiais do Spec Kit

Linux é o ambiente de validação disponível. O suporte a Windows e macOS está previsto; execute as verificações nesses sistemas antes de depender deles.

## Criar um jogo

Na raiz de uma cópia nova do template, inicialize o projeto com nome, slug único e uma porta MCP livre:

    python3 scripts/init_project.py --name "Meu Jogo" --slug meu-jogo --mcp-port 6512
    python3 scripts/setup.py

No Windows, use py -3 no lugar de python3 se necessário. A inicialização aceita --dry-run para mostrar as mudanças sem gravar arquivos. Ela não cria decisões, features, aprovações ou conteúdo de jogo.

O setup instala o servidor MCP local fixado em package-lock.json via npm ci e gera arquivos locais ignorados .codex/config.toml e .mcp.json. Se o Codex perguntar, revise e confie na configuração do projeto nas suas configurações do Codex. O addon do Godot e o servidor usam a mesma porta. Escolha outra porta livre ao executar vários projetos ao mesmo tempo. O template usa 6511.

## Fluxo SDD

Use $sdd-orchestrate para features e sistemas substanciais. O Game Designer conduz toda descoberta de produto e é dono da spec funcional. UI/UX é delegado quando a feature envolver interface ou feedback ao jogador. A implementação começa depois da aprovação explícita da spec, do plano e das tarefas. QA verifica estabilidade técnica; o usuário aprova Game Feel e diversão num Playtest Humano separado. Execute $speckit-converge antes de verificar elegibilidade para main.

Spec Kit v1.1.0 está incluído com scripts e skills Codex. Features são criadas quando necessárias; não há feature fictícia no template. Pequenas manutenções e mudanças documentais podem seguir o fluxo direto descrito em docs/sdd/direct-change-template.md.

## Testes

    python3 scripts/test.py
    python3 scripts/test_workflow.py

No Windows, use py -3 se python3 não estiver no PATH. bash scripts/test.sh permanece como compatibilidade. Saídas de teste e caches do Godot são ignorados pelo Git.

## Componentes de terceiros

Consulte THIRD_PARTY_NOTICES.md para versões, origens e licenças dos componentes. O repositório não concede licença geral para reutilizar os arquivos próprios do template; cada componente de terceiros mantém sua licença.
