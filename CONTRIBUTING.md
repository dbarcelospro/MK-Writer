# Guia de Contribuição — MK Writer 🤝

Agradecemos o seu interesse em contribuir com o **MK Writer**! Nosso objetivo é construir a ferramenta de escrita acadêmica em Markdown mais produtiva, intuitiva e rigorosa para estudantes, pesquisadores e professores.

---

## 🧭 Formas de Contribuição

### 1. 🐛 Reportar Bugs
- Verifique na aba [Issues](https://github.com/dbarcelospro/MK-Writer/issues) se o problema já foi reportado.
- Se for um novo bug, abra uma **Issue** detalhando:
  - Sua distribuição Linux.
  - Comportamento esperado vs. comportamento ocorrido.
  - Passos detalhados para reproduzir o erro.
  - Logs ou capturas de tela quando aplicável.

### 2. 💡 Sugerir Recursos e Modelos Institucionais
- Ideias para novos estilos de citação ou modelos de outras universidades (ex: USP, Unicamp, UFRJ, CAPES).
- Novos atalhos de diagramação acadêmica.
- Melhorias no motor de compilação ou na visualização em tempo real.

### 3. 💻 Desenvolvimento de Código (Pull Request)

1. Faça um **Fork** do repositório ([github.com/dbarcelospro/MK-Writer](https://github.com/dbarcelospro/MK-Writer)).
2. Clone o seu fork:
   ```bash
   git clone https://github.com/SEU_USUARIO/MK-Writer.git
   cd MK-Writer
   ```
3. Crie um ambiente virtual e instale as dependências:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Crie uma branch para sua modificação:
   ```bash
   git checkout -b feature/minha-melhoria
   ```
5. Realize suas modificações, execute os testes e teste a interface:
   ```bash
   python -m unittest discover tests
   python main.py
   ```
6. Envie o commit e abra um **Pull Request**:
   ```bash
   git add .
   git commit -m "feat(editor): adiciona suporte a atalho de tabela"
   git push origin feature/minha-melhoria
   ```

---

## ⚖️ Padrões e Licença

Ao contribuir com o código do **MK Writer**, você concorda que o seu trabalho será disponibilizado sob os termos da licença [MIT License](LICENSE).

Obrigado por ajudar a tornar a produção científica mais acessível e agradável! 🚀
