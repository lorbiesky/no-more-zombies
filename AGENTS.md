# Fluxo de desenvolvimento

Use SDD para novas funcionalidades e sistemas substanciais:

1. Acione $sdd-orchestrate para coordenar o ciclo ou siga estas regras quando a skill não estiver disponível.
2. AGENT_GAME_DESIGNER conduz toda descoberta e comunicação de produto. Ele cria o Epic, mantém o GDD modular e é responsável pela especificação funcional.
3. Para incrementos com UI, HUD, menus ou feedback visual, o Game Designer delega as seções pertinentes ao SUB_AGENT_UI_UX_DESIGNER antes de concluir a especificação.
4. Use $speckit-specify, $speckit-clarify quando restarem dúvidas, $speckit-plan, $speckit-tasks e $speckit-analyze.
5. Não implemente até o usuário aprovar o mesmo pacote de spec, plano e tarefas.
6. DEVELOPER implementa. QA cria e executa testes gdUnit4 e registra evidências. Após QA PASS, o usuário faz Playtest Humano e aprova Game Feel e diversão. Termine com $speckit-converge.
7. Consulte a próxima etapa com python3 scripts/validate_operational_workflow.py --route. Antes de integrar uma feature na main, exija elegibilidade via python3 scripts/validate_operational_workflow.py --check-main --feature-dir <diretório>. Para correções pequenas, manutenção ou documentação sem spec, registre a mudança em docs/sdd/direct-changes/<id>/ e valide com --check-main --direct-change-dir <diretório>.
8. QA executa python3 scripts/test.py (ou bash scripts/test.sh) para as suítes Godot e python3 scripts/test_workflow.py para o validador. No Windows, use py -3 se python3 não estiver no PATH.

O Playtest Humano explícito do usuário é obrigatório para todo incremento de jogo que vá para a main. A versão avaliada precisa corresponder à versão jogável atual. A aprovação do bootstrap SDD começa pendente até o primeiro incremento jogável passar; essa mesma sessão pode aprovar ambos se o usuário registrar as duas decisões explicitamente.

Correções pequenas, manutenção e documentação podem seguir diretamente, sem spec retrospectiva. O portão humano continua aplicável a alterações no jogo. Não invente conteúdo para preencher o GDD.
