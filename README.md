# 🔀 Switch Focus — Estude com Foco!

> Aplicativo de estudos mobile-first com timer Pomodoro, quizzes do ENEM, flashcards com repetição espaçada, teorias com integração Wikipedia, editais históricos do ENEM, shorts educativos do YouTube e gamificação — tudo com temas de anime!

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Flet](https://img.shields.io/badge/Flet-0.84-blue?logo=flutter&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Sobre o Projeto

O **Switch Focus** é um aplicativo de estudos completo desenvolvido em Python com interface gráfica moderna usando **Flet** (mobile-first, 420×800). Foi criado como projeto de extensão universitária com foco em ajudar estudantes a se prepararem para o **ENEM** e **concursos** de forma produtiva e engajante.

O app combina técnicas comprovadas de estudo (Pomodoro, repetição espaçada, quizzes) com elementos de gamificação e temas visuais de animes populares para tornar a experiência de estudo mais motivadora.

> **Migração v3.0**: O app foi migrado de CustomTkinter para **Flet 0.84**, ganhando compatibilidade com mobile (Android/iOS/Web), interface responsiva e arquitetura assíncrona.

---

## ✨ Funcionalidades

### 🏠 Dashboard
- Visão geral do progresso (XP, nível, streak)
- Metas diárias de estudo configuráveis
- Resumo de conquistas e estatísticas

### 🍅 Timer Pomodoro
- Ciclos de foco + pausa configuráveis
- Timer assíncrono (não bloqueia a interface)
- Registro automático de sessões de estudo
- Ganho de XP por sessão completada

### 📋 Gerenciamento de Tarefas
- Criar, editar e excluir tarefas de estudo
- Marcar tarefas como concluídas
- Filtros por status (todas, pendentes, concluídas)

### 📚 Quizzes ENEM
- **171 questões** cobrindo todas as 5 áreas do ENEM:
  - 🔤 Linguagens, Códigos e suas Tecnologias
  - 📐 Matemática e suas Tecnologias
  - 🔬 Ciências da Natureza e suas Tecnologias
  - 🏛️ Ciências Humanas e suas Tecnologias
  - ✏️ Redação
- Integração com API do ENEM e Open Trivia DB
- Feedback imediato com explicações
- Questões oficiais do ENEM por ano

### 📖 Teorias do ENEM
- **26+ tópicos** organizados por 4 áreas de conhecimento
- Resumos teóricos, conceitos-chave e fórmulas
- Dicas específicas para o ENEM
- Tópicos relacionados com navegação direta
- Anotações pessoais por tópico
- Progresso de leitura com rastreamento
- **Pesquisa de artigos via API da Wikipedia** (MediaWiki):
  - Busca inteligente com resultados inline
  - Leitura completa de artigos dentro do app
  - Sugestões rápidas de pesquisa
  - Link para artigo completo na Wikipedia

### 📋 Editais do ENEM (1998–2025)
- **28 edições** do ENEM com dados completos:
  - Tema da redação de cada ano
  - Data da prova e número de inscritos
  - Formato da prova (antigo vs. novo ENEM)
  - Detalhes e curiosidades de cada edição
- Filtros: Todos / ENEM Antigo (98–08) / Novo ENEM (09–25)
- Busca por tema ou ano
- Navegação entre edições (anterior/próxima)
- Botão para pesquisar o tema na Wikipedia

### 🃏 Flashcards com Repetição Espaçada
- **62 flashcards** organizados por área do ENEM
- Algoritmo SM-2 para revisão espaçada inteligente
- Classificação: Fácil / Bom / Difícil / Esqueci
- Agendamento automático de revisões

### 📱 Shorts Educativos
- Feed com vídeos curtos do YouTube por área ENEM
- Filtro por área (5 áreas)
- Abre vídeos no navegador
- 60+ tópicos de busca otimizados

### 📊 Histórico
- Registro completo de sessões de estudo
- Estatísticas de tempo estudado, pomodoros e dias ativos
- Exportação em CSV
- Acompanhamento de progresso e nível

### ⚙️ Configurações
- Personalização do timer Pomodoro (foco, pausa curta, pausa longa)
- Troca de temas visuais (10 temas)
- Metas diárias configuráveis
- Informações do perfil e sobre o app

### 🎮 Gamificação
- **Sistema de XP e Níveis** — ganhe experiência estudando
- **23 Conquistas** desbloqueáveis
- **Streak diário** — mantenha sua sequência de estudos
- **Metas diárias** configuráveis

### 🔑 Sistema de Login
- Cadastro e autenticação local
- Perfis individuais com progresso salvo
- Modo convidado disponível

---

## 🎨 Temas

10 temas visuais inspirados em animes e séries populares:

| Tema | Emoji | Descrição |
|------|-------|-----------|
| **Naruto** | 🍥 | Ninja mais imprevisível da Vila da Folha! |
| **Dragon Ball** | 🟠 | Poder de mais de 8000! Estude como um Saiyajin! |
| **Demon Slayer** | 🔥 | Respire e estude como um Caçador de Demônios! |
| **Attack on Titan** | ⚔️ | Dedique seu coração aos estudos! |
| **My Hero Academia** | 💪 | Plus Ultra! Vá além dos seus limites! |
| **One Piece** | 🏴‍☠️ | O Rei dos Estudantes será você! |
| **Death Note** | 📓 | Escreva seu nome no caderno do sucesso! |
| **Jujutsu Kaisen** | 👁️ | Domínio de estudo expandido! |
| **Stranger Things** | 💡 | O Mundo Invertido dos estudos! |
| **Breaking Bad** | 🧪 | Ciência pura nos estudos! |

---

## 🏗️ Estrutura do Projeto

```
SwitchFocus/
├── main.py                 # Ponto de entrada — ft.run(main)
├── database.py             # Gerenciamento do banco SQLite (14+ tabelas)
├── api_service.py          # Integrações externas (ENEM API, YouTube)
├── content_updater.py      # Atualização automática de conteúdo em background
├── enem_content.py         # Banco expandido de questões e flashcards ENEM
├── enem_syllabus.py        # Conteúdo programático do ENEM (4 áreas, 26+ tópicos)
├── enem_editais.py         # Histórico completo dos editais (1998–2025)
├── themes.py               # 10 temas visuais com paletas de cores
├── requirements.txt        # Dependências do projeto
├── switch_focus.db         # Banco de dados SQLite (gerado automaticamente)
└── views/
    ├── app.py              # App principal (NavigationBar + navegação)
    ├── dashboard_view.py   # Dashboard com estatísticas e metas
    ├── pomodoro_view.py    # Timer Pomodoro (async)
    ├── tasks_view.py       # Gerenciamento de tarefas
    ├── study_view.py       # Quizzes ENEM e concursos
    ├── theory_view.py      # Teorias ENEM + pesquisa Wikipedia API
    ├── enem_editais_view.py# Editais do ENEM (1998–2025)
    ├── flashcards_view.py  # Flashcards com repetição espaçada (SM-2)
    ├── shorts_view.py      # Feed de shorts educativos
    ├── history_view.py     # Histórico de sessões
    ├── settings_view.py    # Configurações do app
    └── login_view.py       # Login e cadastro
```

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11 ou superior
- pip (gerenciador de pacotes)

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/natanfts/ProjetoExtenss-o1.git
cd ProjetoExtenss-o1

# 2. Crie e ative o ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute o aplicativo
python main.py
```

---

## 📦 Dependências

| Pacote | Versão | Uso |
|--------|--------|-----|
| `flet` | ≥ 0.25.0 | Framework UI mobile-first (desktop/web/mobile) |
| `Pillow` | 10.4.0 | Processamento de imagens |
| `requests` | 2.32.3 | Requisições HTTP (APIs, Wikipedia) |
| `youtube-search-python` | 1.6.6 | Busca de vídeos no YouTube |
| `httpx` | ≥ 0.28.0 | Cliente HTTP assíncrono |

---

## 📊 Conteúdo ENEM

O app cobre **todas as áreas** do ENEM com conteúdo abrangente:

| Área | Questões | Flashcards | Tópicos Teoria |
|------|----------|------------|----------------|
| Linguagens | 35+ | 12+ | 7+ |
| Matemática | 40+ | 14+ | 7+ |
| Ciências da Natureza | 45+ | 18+ | 6+ |
| Ciências Humanas | 35+ | 12+ | 6+ |
| Redação | 16+ | 6+ | — |
| **Total** | **171** | **62** | **26+** |

### 📋 Editais do ENEM

| Período | Edições | Formato |
|---------|---------|---------|
| 1998–2008 | 11 edições | ENEM Antigo (63 questões, nota 0–100) |
| 2009–2025 | 17 edições | Novo ENEM (180 questões + TRI, nota 0–1000) |
| **Total** | **28 edições** | Todos com tema de redação documentado |

---

## 🔄 Versionamento

| Versão | Descrição |
|--------|-----------|
| **v1.0** | App Pomodoro de Estudos com Quiz ENEM Real (CustomTkinter) |
| **v2.0** | Gamificação, Dashboard, Flashcards e Metas Diárias |
| **v2.1** | Expansão de conteúdo ENEM + Shorts educativos com feed infinito |
| **v3.0** | **Migração para Flet** — mobile-first, timer async, Teorias ENEM com Wikipedia API, Editais ENEM (1998–2025) |

---

## 🛠️ Tecnologias

- **Python 3.11** — Linguagem principal
- **Flet 0.84** — Framework UI multiplataforma (desktop/web/mobile)
- **SQLite** — Banco de dados local embutido
- **Wikipedia MediaWiki API** — Pesquisa de artigos para teorias
- **youtube-search-python** — Busca de vídeos sem API key
- **Algoritmo SM-2** — Repetição espaçada nos flashcards
- **asyncio** — Timer Pomodoro e operações assíncronas

---

## 👤 Autor

**Natan** — [@natanfts](https://github.com/natanfts)

---

## 📄 Licença

Este projeto é de código aberto e foi desenvolvido como projeto de extensão universitária.
