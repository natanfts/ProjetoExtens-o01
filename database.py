import sqlite3
import hashlib
import json
import os
import hmac
from datetime import datetime

from enem_content import EXPANDED_QUESTIONS, EXPANDED_FLASHCARDS


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            base = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base, "switch_focus.db")
        self.db_path = db_path
        self._init_database()

    # ── conexão ──────────────────────────────────────────────
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ── criação de tabelas ───────────────────────────────────
    def _init_database(self):
        conn = self._conn()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                theme TEXT DEFAULT 'Naruto',
                pomodoro_focus INTEGER DEFAULT 25,
                pomodoro_short INTEGER DEFAULT 5,
                pomodoro_long INTEGER DEFAULT 15,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pendente',
                priority TEXT DEFAULT 'média',
                pomodoros_est INTEGER DEFAULT 1,
                pomodoros_done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_id INTEGER,
                session_type TEXT DEFAULT 'foco',
                duration INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS study_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT DEFAULT 'enem',
                subject TEXT NOT NULL,
                topic TEXT,
                format TEXT DEFAULT 'quiz',
                score REAL DEFAULT 0,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT,
                question TEXT,
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                difficulty TEXT DEFAULT 'médio',
                video_url TEXT,
                video_title TEXT,
                video_channel TEXT,
                content_type TEXT DEFAULT 'quiz',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS update_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_type TEXT NOT NULL,
                category TEXT,
                subject TEXT,
                status TEXT DEFAULT 'success',
                videos_updated INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # Cache de questões reais do ENEM (API enem.dev)
        c.execute("""
            CREATE TABLE IF NOT EXISTS enem_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                question_index INTEGER NOT NULL,
                title TEXT,
                discipline TEXT,
                discipline_name TEXT,
                language TEXT,
                context TEXT,
                question_intro TEXT,
                question_text TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                correct_letter TEXT,
                images TEXT,
                alt_images TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, question_index)
            )
        """)

        # Progresso do quiz ENEM real (por ano)
        c.execute("""
            CREATE TABLE IF NOT EXISTS enem_quiz_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                year INTEGER NOT NULL,
                discipline TEXT,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                score REAL DEFAULT 0,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # ── Gamificação ──────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                emoji TEXT DEFAULT '🏆',
                xp_reward INTEGER DEFAULT 0,
                category TEXT DEFAULT 'geral',
                requirement_type TEXT,
                requirement_value INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_id INTEGER,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (achievement_id) REFERENCES achievements(id),
                UNIQUE(user_id, achievement_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS xp_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER NOT NULL,
                source TEXT NOT NULL,
                description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # ── Flashcards ───────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT DEFAULT 'enem',
                subject TEXT NOT NULL,
                topic TEXT,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                difficulty TEXT DEFAULT 'médio',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS flashcard_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                flashcard_id INTEGER NOT NULL,
                quality INTEGER DEFAULT 0,
                easiness REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 1,
                repetitions INTEGER DEFAULT 0,
                next_review TIMESTAMP,
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (flashcard_id) REFERENCES flashcards(id)
            )
        """)

        # ── Metas Diárias ────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                goal_type TEXT NOT NULL,
                target_value INTEGER NOT NULL,
                current_value INTEGER DEFAULT 0,
                date TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, goal_type, date)
            )
        """)

        # ── Progresso de Teoria (editais) ─────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS theory_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                area TEXT NOT NULL,
                topic_title TEXT NOT NULL,
                read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, area, topic_title)
            )
        """)

        conn.commit()

        # Migrar colunas extras em users (XP, streak, etc.)
        self._migrate_users_gamification(conn)

        # Seed de conquistas
        c.execute("SELECT COUNT(*) FROM achievements")
        if c.fetchone()[0] == 0:
            self._seed_achievements(conn)

        c.execute("SELECT COUNT(*) FROM content")
        if c.fetchone()[0] == 0:
            self._seed_content(conn)

        # Seed flashcards padrão
        c.execute("SELECT COUNT(*) FROM flashcards WHERE user_id IS NULL")
        if c.fetchone()[0] == 0:
            self._seed_flashcards(conn)

        # Seed de conteúdo expandido ENEM (migração segura)
        self._seed_expanded_content(conn)

        conn.close()

    # ── migração gamificação ─────────────────────────────────
    def _migrate_users_gamification(self, conn):
        """Adiciona colunas de gamificação à tabela users se não existirem."""
        c = conn.cursor()
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        migrations = [
            ("xp", "INTEGER DEFAULT 0"),
            ("level", "INTEGER DEFAULT 1"),
            ("streak_days", "INTEGER DEFAULT 0"),
            ("last_active_date", "TEXT"),
            ("longest_streak", "INTEGER DEFAULT 0"),
            ("daily_xp_goal", "INTEGER DEFAULT 100"),
            ("daily_pomodoro_goal", "INTEGER DEFAULT 4"),
            ("daily_quiz_goal", "INTEGER DEFAULT 10"),
        ]
        for col, typedef in migrations:
            if col not in cols:
                c.execute(f"ALTER TABLE users ADD COLUMN {col} {typedef}")
        conn.commit()

        # Migração: coluna deadline na tabela tasks
        task_cols = [r[1]
                     for r in c.execute("PRAGMA table_info(tasks)").fetchall()]
        if "deadline" not in task_cols:
            c.execute("ALTER TABLE tasks ADD COLUMN deadline TEXT")
            conn.commit()

    # ── Seed de conquistas ───────────────────────────────────
    def _seed_achievements(self, conn):
        achievements = [
            # Pomodoro
            ("first_pomodoro", "Primeiro Pomodoro!", "Complete sua primeira sessão de foco",
             "🍅", 25, "pomodoro", "pomodoros_completed", 1),
            ("pomodoro_10", "Focado", "Complete 10 sessões de foco",
             "🔥", 50, "pomodoro", "pomodoros_completed", 10),
            ("pomodoro_50", "Mestre do Foco", "Complete 50 sessões de foco",
             "🧘", 150, "pomodoro", "pomodoros_completed", 50),
            ("pomodoro_100", "Lenda do Pomodoro", "Complete 100 sessões de foco",
             "💎", 300, "pomodoro", "pomodoros_completed", 100),
            ("pomodoro_marathon", "Maratonista", "Complete 8 pomodoros em um dia",
             "🏃", 100, "pomodoro", "daily_pomodoros", 8),
            # Quiz
            ("first_quiz", "Primeira Questão!", "Responda sua primeira questão",
             "📝", 15, "quiz", "quizzes_completed", 1),
            ("quiz_50", "Estudioso", "Responda 50 questões",
             "📚", 75, "quiz", "quizzes_completed", 50),
            ("quiz_200", "Enciclopédia", "Responda 200 questões",
             "🎓", 200, "quiz", "quizzes_completed", 200),
            ("perfect_quiz", "Nota Máxima!", "Acerte 100% em um quiz",
             "⭐", 100, "quiz", "perfect_score", 1),
            ("enem_warrior", "Guerreiro do ENEM", "Complete 5 simulados ENEM",
             "🎯", 150, "quiz", "enem_quizzes", 5),
            # Streak
            ("streak_3", "Consistente", "Estude 3 dias seguidos",
             "📅", 50, "streak", "streak_days", 3),
            ("streak_7", "Semana Perfeita", "Estude 7 dias seguidos",
             "🌟", 150, "streak", "streak_days", 7),
            ("streak_30", "Mês de Ouro", "Estude 30 dias seguidos",
             "👑", 500, "streak", "streak_days", 30),
            # Flashcards
            ("first_flashcard", "Primeiro Flashcard!", "Crie seu primeiro flashcard",
             "🃏", 15, "flashcard", "flashcards_created", 1),
            ("flashcard_master", "Memória de Elefante", "Revise 100 flashcards",
             "🧠", 100, "flashcard", "flashcards_reviewed", 100),
            # Tarefas
            ("first_task", "Organizado", "Complete sua primeira tarefa",
             "✅", 20, "task", "tasks_completed", 1),
            ("task_25", "Produtivo", "Complete 25 tarefas",
             "🚀", 100, "task", "tasks_completed", 25),
            # Níveis
            ("level_5", "Estudante Dedicado", "Alcance o nível 5",
             "🎖️", 0, "level", "level_reached", 5),
            ("level_10", "Veterano", "Alcance o nível 10",
             "🏅", 0, "level", "level_reached", 10),
            ("level_25", "Mestre dos Estudos", "Alcance o nível 25",
             "🏆", 0, "level", "level_reached", 25),
            # Horas
            ("hours_5", "5 Horas de Estudo", "Acumule 5 horas de foco",
             "⏰", 75, "hours", "focus_hours", 5),
            ("hours_25", "25 Horas de Estudo", "Acumule 25 horas de foco",
             "⌛", 200, "hours", "focus_hours", 25),
            ("hours_100", "100 Horas de Estudo", "Acumule 100 horas de foco",
             "⏳", 500, "hours", "focus_hours", 100),
        ]
        for a in achievements:
            conn.execute(
                """INSERT INTO achievements (key, title, description, emoji, xp_reward,
                   category, requirement_type, requirement_value)
                   VALUES (?,?,?,?,?,?,?,?)""", a
            )
        conn.commit()

    # ── Seed de flashcards padrão ────────────────────────────
    def _seed_flashcards(self, conn):
        cards = [
            # Matemática
            ("enem", "Matemática", "Fórmulas",
             "Área do triângulo", "(base × altura) / 2", "fácil"),
            ("enem", "Matemática", "Fórmulas",
             "Área do círculo", "π × r²", "fácil"),
            ("enem", "Matemática", "Fórmulas", "Teorema de Pitágoras",
             "a² = b² + c² (hipotenusa² = cateto² + cateto²)", "fácil"),
            ("enem", "Matemática", "Fórmulas", "Fórmula de Bhaskara",
             "x = (-b ± √Δ) / 2a, onde Δ = b² - 4ac", "médio"),
            ("enem", "Matemática", "Fórmulas",
             "Volume da esfera", "(4/3) × π × r³", "médio"),
            ("enem", "Matemática", "Fórmulas",
             "Progressão Aritmética (termo geral)", "aₙ = a₁ + (n-1) × r", "médio"),
            ("enem", "Matemática", "Fórmulas",
             "Juros compostos", "M = C × (1 + i)ⁿ", "difícil"),
            # Física
            ("enem", "Ciências da Natureza", "Física", "2ª Lei de Newton",
             "F = m × a (Força = massa × aceleração)", "fácil"),
            ("enem", "Ciências da Natureza", "Física", "Velocidade média",
             "v = Δs / Δt (variação do espaço / variação do tempo)", "fácil"),
            ("enem", "Ciências da Natureza", "Física",
             "Energia cinética", "Ec = (m × v²) / 2", "médio"),
            ("enem", "Ciências da Natureza", "Física", "Lei de Ohm",
             "V = R × I (Tensão = Resistência × Corrente)", "médio"),
            # Química
            ("enem", "Ciências da Natureza", "Química", "O que é pH?",
             "Potencial hidrogeniônico. pH < 7 = ácido, pH = 7 = neutro, pH > 7 = básico", "fácil"),
            ("enem", "Ciências da Natureza", "Química", "Lei de Lavoisier",
             "Na natureza nada se cria, nada se perde, tudo se transforma (conservação de massa)", "fácil"),
            ("enem", "Ciências da Natureza", "Química", "Número de Avogadro",
             "6,022 × 10²³ (número de entidades em 1 mol)", "médio"),
            # Biologia
            ("enem", "Ciências da Natureza", "Biologia", "Mitose vs Meiose",
             "Mitose: 2 células iguais (2n). Meiose: 4 células diferentes (n) - gametas", "médio"),
            ("enem", "Ciências da Natureza", "Biologia", "Fotossíntese (equação)",
             "6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂ (luz + clorofila)", "médio"),
            # História
            ("enem", "Ciências Humanas", "História", "Proclamação da República",
             "15 de novembro de 1889 — Marechal Deodoro da Fonseca", "fácil"),
            ("enem", "Ciências Humanas", "História", "Independência do Brasil",
             "7 de setembro de 1822 — Dom Pedro I às margens do Ipiranga", "fácil"),
            ("enem", "Ciências Humanas", "História", "Revolução Francesa",
             "1789 — Queda da Bastilha. Lema: Liberdade, Igualdade, Fraternidade", "médio"),
            # Geografia
            ("enem", "Ciências Humanas", "Geografia", "Camadas da Terra",
             "Crosta, Manto, Núcleo externo, Núcleo interno", "fácil"),
            ("enem", "Ciências Humanas", "Geografia", "Biomas brasileiros",
             "Amazônia, Cerrado, Mata Atlântica, Caatinga, Pampa, Pantanal", "fácil"),
            # Português / Redação
            ("enem", "Linguagens", "Gramática", "Tipos de 'porquê'",
             "Por que (pergunta), Porque (resposta), Por quê (fim de frase), Porquê (substantivo)", "médio"),
            ("enem", "Redação", "Competências", "5 competências da redação ENEM",
             "C1: Norma culpa\nC2: Compreensão do tema\nC3: Argumentação\nC4: Coesão\nC5: Proposta de intervenção", "médio"),
        ]
        for card in cards:
            conn.execute(
                """INSERT INTO flashcards (category, subject, topic, front, back, difficulty)
                   VALUES (?,?,?,?,?,?)""", card
            )
        conn.commit()

    # ── Seed de conteúdo expandido ENEM ──────────────────────
    def _seed_expanded_content(self, conn):
        """
        Adiciona questões e flashcards expandidos do ENEM.
        Usa INSERT OR IGNORE para não duplicar conteúdo já existente.
        Verifica por uma flag na tabela update_log para rodar só uma vez.
        """
        c = conn.cursor()

        # Verificar se já rodou a expansão v2.1
        row = c.execute(
            "SELECT 1 FROM update_log WHERE update_type='content_expansion_v2.1' AND status='success'"
        ).fetchone()
        if row:
            return  # já expandido

        added_q = 0
        added_f = 0

        # ── Inserir questões expandidas ──────────────────────
        for q in EXPANDED_QUESTIONS:
            try:
                # Verificar se questão já existe (por texto da pergunta)
                existing = c.execute(
                    "SELECT 1 FROM content WHERE question=? AND category=?",
                    (q[3], q[0]),
                ).fetchone()
                if not existing:
                    c.execute(
                        """INSERT INTO content
                           (category, subject, topic, question, options,
                            correct_answer, explanation, difficulty, content_type)
                           VALUES (?,?,?,?,?,?,?,?,'quiz')""", q
                    )
                    added_q += 1
            except Exception:
                continue

        # ── Inserir flashcards expandidos ────────────────────
        for f in EXPANDED_FLASHCARDS:
            try:
                existing = c.execute(
                    "SELECT 1 FROM flashcards WHERE front=? AND category=? AND user_id IS NULL",
                    (f[3], f[0]),
                ).fetchone()
                if not existing:
                    c.execute(
                        """INSERT INTO flashcards
                           (category, subject, topic, front, back, difficulty)
                           VALUES (?,?,?,?,?,?)""", f
                    )
                    added_f += 1
            except Exception:
                continue

        # Registrar que a expansão foi feita
        c.execute(
            """INSERT INTO update_log (update_type, status, videos_updated, completed_at)
               VALUES ('content_expansion_v2.1', 'success', ?, ?)""",
            (added_q + added_f, datetime.now().isoformat()),
        )
        conn.commit()

    # ── SEED de conteúdo ─────────────────────────────────────
    def _seed_content(self, conn):
        questions = [
            # ── ENEM – Linguagens ───────────────────────────
            ("enem", "Linguagens", "Interpretação de Texto",
             "Qual figura de linguagem consiste em atribuir características humanas a seres inanimados?",
             json.dumps(["Metáfora", "Prosopopeia", "Hipérbole", "Metonímia"]),
             "Prosopopeia",
             "Prosopopeia (ou personificação) atribui qualidades humanas a objetos, animais ou fenômenos.",
             "fácil"),
            ("enem", "Linguagens", "Gramática",
             "Na oração 'Os alunos cujos pais compareceram foram elogiados', a palavra 'cujos' é:",
             json.dumps(["Pronome relativo", "Conjunção",
                        "Pronome demonstrativo", "Advérbio"]),
             "Pronome relativo",
             "'Cujos' é pronome relativo que estabelece relação de posse entre antecedente e consequente.",
             "médio"),
            ("enem", "Linguagens", "Literatura",
             "O Modernismo brasileiro teve como marco inicial a Semana de Arte Moderna de:",
             json.dumps(["1920", "1922", "1925", "1930"]),
             "1922",
             "A Semana de Arte Moderna aconteceu em fevereiro de 1922 no Teatro Municipal de São Paulo.",
             "fácil"),
            ("enem", "Linguagens", "Literatura",
             "Qual autor é considerado o principal representante do Realismo no Brasil?",
             json.dumps(["José de Alencar", "Machado de Assis",
                        "Castro Alves", "Gonçalves Dias"]),
             "Machado de Assis",
             "Machado de Assis é o maior nome do Realismo brasileiro, com obras como Dom Casmurro e Memórias Póstumas de Brás Cubas.",
             "fácil"),
            ("enem", "Linguagens", "Gramática",
             "Qual alternativa apresenta um exemplo correto de crase?",
             json.dumps(["Fui à escola", "Fui à casa",
                        "Refiro-me à você", "Chegou à pé"]),
             "Fui à escola",
             "Usa-se crase antes de palavras femininas determinadas. 'À escola' está correto pois há artigo definido.",
             "médio"),

            # ── ENEM – Matemática ──────────────────────────
            ("enem", "Matemática", "Porcentagem",
             "Um produto que custava R$ 200,00 teve um desconto de 15%. Qual o novo preço?",
             json.dumps(["R$ 170,00", "R$ 180,00", "R$ 175,00", "R$ 185,00"]),
             "R$ 170,00",
             "15% de 200 = 30. Portanto: 200 - 30 = R$ 170,00.",
             "fácil"),
            ("enem", "Matemática", "Geometria",
             "Qual a área de um triângulo com base 10 cm e altura 6 cm?",
             json.dumps(["60 cm²", "30 cm²", "16 cm²", "36 cm²"]),
             "30 cm²",
             "Área do triângulo = (base × altura) / 2 = (10 × 6) / 2 = 30 cm².",
             "fácil"),
            ("enem", "Matemática", "Probabilidade",
             "Ao lançar dois dados, qual a probabilidade de obter soma igual a 7?",
             json.dumps(["1/6", "1/12", "1/4", "1/36"]),
             "1/6",
             "Existem 6 combinações que somam 7 de um total de 36 possibilidades: 6/36 = 1/6.",
             "médio"),
            ("enem", "Matemática", "Funções",
             "Dada f(x) = 2x + 3, qual o valor de f(5)?",
             json.dumps(["10", "13", "15", "8"]),
             "13",
             "f(5) = 2(5) + 3 = 10 + 3 = 13.",
             "fácil"),
            ("enem", "Matemática", "Estatística",
             "A média aritmética de 4, 6, 8, 10 e 12 é:",
             json.dumps(["7", "8", "9", "10"]),
             "8",
             "Média = (4+6+8+10+12)/5 = 40/5 = 8.",
             "fácil"),
            ("enem", "Matemática", "Geometria",
             "O volume de um cubo com aresta de 3 cm é:",
             json.dumps(["9 cm³", "18 cm³", "27 cm³", "81 cm³"]),
             "27 cm³",
             "Volume do cubo = a³ = 3³ = 27 cm³.",
             "fácil"),

            # ── ENEM – Ciências da Natureza ─────────────────
            ("enem", "Ciências da Natureza", "Física - Leis de Newton",
             "A Primeira Lei de Newton é conhecida como Lei da:",
             json.dumps(["Ação e Reação", "Inércia",
                        "Gravitação", "Conservação"]),
             "Inércia",
             "A 1ª Lei de Newton (Lei da Inércia) afirma que um corpo em repouso tende a permanecer em repouso.",
             "fácil"),
            ("enem", "Ciências da Natureza", "Química - Tabela Periódica",
             "Qual elemento químico tem o símbolo 'Fe'?",
             json.dumps(["Flúor", "Ferro", "Fósforo", "Frâncio"]),
             "Ferro",
             "Fe vem do latim 'Ferrum', que significa ferro. Número atômico 26.",
             "fácil"),
            ("enem", "Ciências da Natureza", "Biologia - Ecologia",
             "O conjunto de seres vivos de uma mesma espécie que vivem em determinada região é chamado de:",
             json.dumps(["Comunidade", "Ecossistema", "População", "Bioma"]),
             "População",
             "População é o conjunto de indivíduos da mesma espécie em uma determinada área.",
             "fácil"),
            ("enem", "Ciências da Natureza", "Biologia - Genética",
             "Qual é a molécula responsável por carregar a informação genética?",
             json.dumps(["RNA", "DNA", "Proteína", "Lipídio"]),
             "DNA",
             "O DNA (ácido desoxirribonucleico) carrega toda a informação genética dos seres vivos.",
             "fácil"),
            ("enem", "Ciências da Natureza", "Física - Termodinâmica",
             "A escala de temperatura em que a água ferve a 373 K é:",
             json.dumps(["Celsius", "Fahrenheit", "Kelvin", "Rankine"]),
             "Kelvin",
             "Na escala Kelvin, a água ferve a 373 K (equivalente a 100°C).",
             "médio"),
            ("enem", "Ciências da Natureza", "Química - Reações",
             "Uma reação de combustão completa de um hidrocarboneto produz:",
             json.dumps(["CO e H2", "CO2 e H2O", "CO e H2O", "C e H2O"]),
             "CO2 e H2O",
             "Combustão completa: hidrocarboneto + O2 → CO2 + H2O.",
             "médio"),
            ("enem", "Ciências da Natureza", "Biologia - Citologia",
             "A organela responsável pela respiração celular é:",
             json.dumps(["Ribossomo", "Complexo de Golgi",
                        "Mitocôndria", "Lisossomo"]),
             "Mitocôndria",
             "A mitocôndria é a organela responsável pela respiração celular aeróbica e produção de ATP.",
             "fácil"),

            # ── ENEM – Ciências Humanas ────────────────────
            ("enem", "Ciências Humanas", "História - Rev. Industrial",
             "A Revolução Industrial teve início em qual país?",
             json.dumps(
                 ["França", "Alemanha", "Inglaterra", "Estados Unidos"]),
             "Inglaterra",
             "A Revolução Industrial começou na Inglaterra no século XVIII.",
             "fácil"),
            ("enem", "Ciências Humanas", "Geografia - Globalização",
             "Qual bloco econômico o Brasil faz parte como membro fundador?",
             json.dumps(["União Europeia", "NAFTA", "Mercosul", "APEC"]),
             "Mercosul",
             "O Mercosul foi fundado em 1991 pelo Tratado de Assunção, com Brasil, Argentina, Paraguai e Uruguai.",
             "fácil"),
            ("enem", "Ciências Humanas", "Filosofia",
             "O filósofo grego considerado o 'pai da filosofia ocidental' é:",
             json.dumps(["Platão", "Aristóteles",
                        "Sócrates", "Tales de Mileto"]),
             "Sócrates",
             "Sócrates é considerado o pai da filosofia ocidental. Seu método era baseado no diálogo e questionamento.",
             "fácil"),
            ("enem", "Ciências Humanas", "Sociologia",
             "Qual sociólogo é autor do conceito de 'fato social'?",
             json.dumps(["Max Weber", "Karl Marx",
                        "Émile Durkheim", "Auguste Comte"]),
             "Émile Durkheim",
             "Durkheim definiu fato social como maneiras de agir, pensar e sentir exteriores ao indivíduo.",
             "médio"),
            ("enem", "Ciências Humanas", "História - Brasil",
             "A Proclamação da República do Brasil aconteceu em:",
             json.dumps(["1822", "1889", "1891", "1888"]),
             "1889",
             "A República foi proclamada em 15 de novembro de 1889 pelo Marechal Deodoro da Fonseca.",
             "fácil"),
            ("enem", "Ciências Humanas", "Geografia - Brasil",
             "Qual é o maior bioma brasileiro em extensão territorial?",
             json.dumps(["Cerrado", "Mata Atlântica", "Amazônia", "Caatinga"]),
             "Amazônia",
             "A Amazônia ocupa cerca de 49% do território brasileiro, sendo o maior bioma do país.",
             "fácil"),

            # ── ENEM – Redação ─────────────────────────────
            ("enem", "Redação", "Estrutura",
             "Quantos parágrafos tem a estrutura padrão de uma redação dissertativa-argumentativa do ENEM?",
             json.dumps(["3", "4", "5", "6"]),
             "5",
             "Introdução + 2 parágrafos de desenvolvimento + conclusão com proposta de intervenção = ~4-5 parágrafos. O padrão recomendado é 5.",
             "fácil"),
            ("enem", "Redação", "Competências",
             "Quantas competências são avaliadas na redação do ENEM?",
             json.dumps(["3", "4", "5", "6"]),
             "5",
             "São 5 competências, cada uma valendo até 200 pontos, totalizando 1000 pontos.",
             "fácil"),

            # ── Concursos ──────────────────────────────────
            ("concursos", "Português", "Concordância",
             "Na frase 'Faz dois anos que não o vejo', o verbo 'fazer' está:",
             json.dumps(["No plural", "No singular (impessoal)",
                        "No gerúndio", "No subjuntivo"]),
             "No singular (impessoal)",
             "O verbo 'fazer' indicando tempo decorrido é impessoal, ficando sempre na 3ª pessoa do singular.",
             "médio"),
            ("concursos", "Raciocínio Lógico", "Proposições",
             "A negação de 'Todos os alunos passaram' é:",
             json.dumps(["Nenhum aluno passou", "Pelo menos um aluno não passou",
                        "Todos reprovaram", "Alguns passaram"]),
             "Pelo menos um aluno não passou",
             "A negação de 'Todo A é B' é 'Existe pelo menos um A que não é B'.",
             "médio"),
            ("concursos", "Informática", "Hardware",
             "Qual componente é responsável pelo processamento de dados no computador?",
             json.dumps(["HD", "CPU", "RAM", "Placa-mãe"]),
             "CPU",
             "A CPU (Unidade Central de Processamento) é o 'cérebro' do computador.",
             "fácil"),
            ("concursos", "Direito Constitucional", "Direitos Fundamentais",
             "Os direitos e garantias fundamentais estão previstos no artigo 5º da Constituição Federal de:",
             json.dumps(["1967", "1946", "1988", "1891"]),
             "1988",
             "A Constituição Federal de 1988, conhecida como 'Constituição Cidadã', traz os direitos fundamentais.",
             "fácil"),
            ("concursos", "Atualidades", "Brasil",
             "O Sistema Único de Saúde (SUS) foi criado pela Constituição de:",
             json.dumps(["1946", "1967", "1988", "1991"]),
             "1988",
             "O SUS foi criado pela CF/88 e regulamentado pelas Leis 8.080/90 e 8.142/90.",
             "médio"),
            ("concursos", "Raciocínio Lógico", "Sequências",
             "Qual o próximo número da sequência: 2, 6, 18, 54, ...?",
             json.dumps(["108", "162", "72", "216"]),
             "162",
             "É uma progressão geométrica de razão 3: 54 × 3 = 162.",
             "médio"),
            ("concursos", "Português", "Interpretação",
             "A coesão textual é garantida pelo uso de:",
             json.dumps(["Parágrafos longos", "Conectivos e pronomes",
                        "Palavras difíceis", "Repetição de ideias"]),
             "Conectivos e pronomes",
             "Conectivos (conjunções, preposições) e pronomes são os principais elementos de coesão textual.",
             "fácil"),
            ("concursos", "Informática", "Internet",
             "O protocolo utilizado para navegação segura na web é:",
             json.dumps(["HTTP", "FTP", "HTTPS", "SMTP"]),
             "HTTPS",
             "HTTPS (Hyper Text Transfer Protocol Secure) usa criptografia SSL/TLS para navegação segura.",
             "fácil"),
        ]

        for q in questions:
            conn.execute("""
                INSERT INTO content (category, subject, topic, question, options,
                    correct_answer, explanation, difficulty, content_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'quiz')
            """, q)

        videos = [
            # ── ENEM Videos ─────────────────────────────────
            ("enem", "Linguagens", "Interpretação de Texto",
             "https://www.youtube.com/watch?v=7YBA9h2-438",
             "Leitura e Interpretação de Textos - ENEM", "Brasil Escola"),
            ("enem", "Linguagens", "Gramática",
             "https://www.youtube.com/watch?v=-rKt0k-BXZ0",
             "Gramática para PASSAR no ENEM", "Stoodi"),
            ("enem", "Matemática", "Porcentagem",
             "https://www.youtube.com/watch?v=CERiIwParX4",
             "Porcentagem: Teoria e Exemplos - Aula 29", "Professor Ferretto"),
            ("enem", "Matemática", "Geometria",
             "https://www.youtube.com/watch?v=0CnUdzmpO8E",
             "Geometria Plana: Introdução – Ângulos", "Professor Ferretto"),
            ("enem", "Matemática", "Funções",
             "https://www.youtube.com/watch?v=hdMFlAv5GkU",
             "Função do 1º Grau (Função Afim): Conceitos Iniciais", "Professor Ferretto"),
            ("enem", "Ciências da Natureza", "Física - Cinemática",
             "https://www.youtube.com/watch?v=M2urmZToedM",
             "Movimento Uniforme – Teoria e Exemplos", "Me Salva!"),
            ("enem", "Ciências da Natureza", "Química - Estequiometria",
             "https://www.youtube.com/watch?v=8FVJXszOmUw",
             "Introdução à Estequiometria / Cálculo Estequiométrico", "Marcelão da Química"),
            ("enem", "Ciências da Natureza", "Biologia - Ecologia",
             "https://www.youtube.com/watch?v=XvdePktAui8",
             "Conceitos Básicos da Ecologia", "Biologia Total (Paulo Jubilut)"),
            ("enem", "Ciências Humanas", "História - Brasil Colônia",
             "https://www.youtube.com/watch?v=VofLIlRK6vI",
             "Brasil Colônia – Economia Colonial (Revisão ENEM)", "Se Liga Nessa História"),
            ("enem", "Ciências Humanas", "Geografia - Urbanização",
             "https://www.youtube.com/watch?v=v15_Y7oQ9K8",
             "Urbanização Brasileira: Causas, Consequências e Problemas", "Geografilia"),
            ("enem", "Ciências Humanas", "Filosofia",
             "https://www.youtube.com/watch?v=NCVQKQuVXmA",
             "Filósofos no ENEM: Sócrates, Platão, Tales e Aristóteles", "Descomplica"),
            ("enem", "Redação", "Estrutura",
             "https://www.youtube.com/watch?v=dcna77bVXAU",
             "Dicas para Escrever uma Redação Nota 1000 no ENEM", "Descomplica"),
            # ── Concursos Videos ────────────────────────────
            ("concursos", "Português", "Concordância",
             "https://www.youtube.com/watch?v=jdqhnVUvqOc",
             "Concordância Verbal – Teoria e Questões para Concurso", "Prof. Álvaro Ferreira"),
            ("concursos", "Raciocínio Lógico", "Proposições",
             "https://www.youtube.com/watch?v=Q-6-lJhawNA",
             "Raciocínio Lógico para Concursos", "Estratégia Concursos"),
            ("concursos", "Direito Constitucional", "Princípios",
             "https://www.youtube.com/watch?v=4JE6E9-7CdU",
             "Princípios Fundamentais – Direito Constitucional", "Estratégia Concursos"),
            ("concursos", "Informática", "Conceitos Básicos",
             "https://www.youtube.com/watch?v=pY7pM6JOxMU",
             "Informática para Concursos – Aula Completa", "Gran Cursos Online"),
        ]

        for v in videos:
            conn.execute("""
                INSERT INTO content (category, subject, topic, video_url,
                    video_title, video_channel, content_type)
                VALUES (?, ?, ?, ?, ?, ?, 'video')
            """, v)

        conn.commit()

    # ── Usuários ─────────────────────────────────────────────
    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """
        Verifica senha em formato atual (sha256 simples) e legado (salt$hash).
        """
        if not stored_hash:
            return False

        current = self._hash(password)
        if hmac.compare_digest(stored_hash, current):
            return True

        if "$" not in stored_hash:
            return False

        parts = stored_hash.split("$")
        if len(parts) != 2:
            return False

        salt, legacy_hash = parts
        if not salt or not legacy_hash:
            return False

        # Compatibilidade com versões antigas.
        candidates = [
            hashlib.sha256((salt + password).encode()).hexdigest(),
            hashlib.sha256((password + salt).encode()).hexdigest(),
            hashlib.sha256((salt + ":" + password).encode()).hexdigest(),
            hashlib.sha256((password + ":" + salt).encode()).hexdigest(),
        ]
        return any(hmac.compare_digest(c, legacy_hash) for c in candidates)

    def create_user(self, username, password, display_name=None):
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash, display_name) VALUES (?,?,?)",
                (username, self._hash(password), display_name or username),
            )
            conn.commit()
            user = conn.execute(
                "SELECT * FROM users WHERE username=?", (username,)
            ).fetchone()
            return dict(user)
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def authenticate(self, username, password):
        conn = self._conn()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE username=?",
                (username,),
            ).fetchone()
            if not user:
                return None

            user_dict = dict(user)
            stored_hash = user_dict.get("password_hash", "")
            if not self._verify_password(password, stored_hash):
                return None

            # Migra hash legado para o formato atual após login válido.
            if "$" in stored_hash:
                new_hash = self._hash(password)
                conn.execute(
                    "UPDATE users SET password_hash=? WHERE id=?",
                    (new_hash, user_dict["id"]),
                )
                conn.commit()
                user_dict["password_hash"] = new_hash

            return user_dict
        finally:
            conn.close()

    def update_user_theme(self, user_id, theme):
        conn = self._conn()
        conn.execute("UPDATE users SET theme=? WHERE id=?", (theme, user_id))
        conn.commit()
        conn.close()

    def update_user_pomodoro(self, user_id, focus, short_break, long_break):
        conn = self._conn()
        conn.execute(
            "UPDATE users SET pomodoro_focus=?, pomodoro_short=?, pomodoro_long=? WHERE id=?",
            (focus, short_break, long_break, user_id),
        )
        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = self._conn()
        user = conn.execute("SELECT * FROM users WHERE id=?",
                            (user_id,)).fetchone()
        conn.close()
        return dict(user) if user else None

    # ── Tarefas ──────────────────────────────────────────────
    def create_task(self, title, description="", priority="média", pomodoros_est=1, user_id=None, deadline=None):
        conn = self._conn()
        conn.execute(
            """INSERT INTO tasks (user_id, title, description, priority, pomodoros_est, deadline)
               VALUES (?,?,?,?,?,?)""",
            (user_id, title, description, priority, pomodoros_est, deadline),
        )
        conn.commit()
        task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return task_id

    def get_tasks(self, user_id=None, status=None):
        conn = self._conn()
        q = "SELECT * FROM tasks WHERE user_id IS ?"
        params = [user_id]
        if status:
            q += " AND status=?"
            params.append(status)
        q += " ORDER BY CASE priority WHEN 'alta' THEN 1 WHEN 'média' THEN 2 ELSE 3 END, created_at DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_task(self, task_id, **kwargs):
        conn = self._conn()
        sets = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [task_id]
        conn.execute(f"UPDATE tasks SET {sets} WHERE id=?", vals)
        conn.commit()
        conn.close()

    def complete_task(self, task_id):
        conn = self._conn()
        conn.execute(
            "UPDATE tasks SET status='concluída', completed_at=? WHERE id=?",
            (datetime.now().isoformat(), task_id),
        )
        conn.commit()
        conn.close()

    def delete_task(self, task_id):
        conn = self._conn()
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        conn.close()

    def increment_task_pomodoro(self, task_id):
        conn = self._conn()
        conn.execute(
            "UPDATE tasks SET pomodoros_done = pomodoros_done + 1 WHERE id=?", (task_id,))
        conn.commit()
        conn.close()

    # ── Sessões Pomodoro ─────────────────────────────────────
    def save_session(self, session_type, duration, started_at, user_id=None, task_id=None):
        conn = self._conn()
        conn.execute(
            """INSERT INTO pomodoro_sessions
               (user_id, task_id, session_type, duration, started_at)
               VALUES (?,?,?,?,?)""",
            (user_id, task_id, session_type, duration, started_at),
        )
        conn.commit()
        conn.close()

    def get_sessions(self, user_id=None, limit=50):
        conn = self._conn()
        rows = conn.execute(
            """SELECT ps.*, t.title as task_title
               FROM pomodoro_sessions ps
               LEFT JOIN tasks t ON ps.task_id = t.id
               WHERE ps.user_id IS ?
               ORDER BY ps.completed_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_session_stats(self, user_id=None):
        conn = self._conn()
        row = conn.execute(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN session_type='foco' THEN 1 ELSE 0 END) as focus_count,
                SUM(CASE WHEN session_type='foco' THEN duration ELSE 0 END) as focus_minutes,
                COUNT(DISTINCT DATE(completed_at)) as days_active
               FROM pomodoro_sessions WHERE user_id IS ?""",
            (user_id,),
        ).fetchone()
        conn.close()
        return dict(row)

    # ── Progresso de Estudo ──────────────────────────────────
    def save_study_progress(self, subject, topic, fmt, score, total, correct, category="enem", user_id=None):
        conn = self._conn()
        conn.execute(
            """INSERT INTO study_progress
               (user_id, category, subject, topic, format, score, total_questions, correct_answers)
               VALUES (?,?,?,?,?,?,?,?)""",
            (user_id, category, subject, topic, fmt, score, total, correct),
        )
        conn.commit()
        conn.close()

    def get_study_stats(self, user_id=None, category=None):
        conn = self._conn()
        q = """SELECT subject,
                      COUNT(*) as sessions,
                      AVG(score) as avg_score,
                      SUM(total_questions) as total_q,
                      SUM(correct_answers) as total_correct
               FROM study_progress WHERE user_id IS ?"""
        params = [user_id]
        if category:
            q += " AND category=?"
            params.append(category)
        q += " GROUP BY subject ORDER BY sessions DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Conteúdo ─────────────────────────────────────────────
    def get_subjects(self, category="enem", content_type="quiz"):
        conn = self._conn()
        rows = conn.execute(
            "SELECT DISTINCT subject FROM content WHERE category=? AND content_type=? ORDER BY subject",
            (category, content_type),
        ).fetchall()
        conn.close()
        return [r["subject"] for r in rows]

    def get_topics(self, category, subject, content_type="quiz"):
        conn = self._conn()
        rows = conn.execute(
            "SELECT DISTINCT topic FROM content WHERE category=? AND subject=? AND content_type=? ORDER BY topic",
            (category, subject, content_type),
        ).fetchall()
        conn.close()
        return [r["topic"] for r in rows]

    def get_questions(self, category, subject, topic=None, limit=10):
        conn = self._conn()
        q = "SELECT * FROM content WHERE category=? AND subject=? AND content_type='quiz'"
        params = [category, subject]
        if topic:
            q += " AND topic=?"
            params.append(topic)
        q += " ORDER BY RANDOM() LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_videos(self, category, subject, topic=None):
        conn = self._conn()
        q = "SELECT * FROM content WHERE category=? AND subject=? AND content_type='video'"
        params = [category, subject]
        if topic:
            q += " AND topic=?"
            params.append(topic)
        q += " ORDER BY topic"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def search_content(self, query, content_type=None):
        conn = self._conn()
        q = """SELECT * FROM content
               WHERE (question LIKE ? OR topic LIKE ? OR subject LIKE ?
                      OR video_title LIKE ?)"""
        params = [f"%{query}%"] * 4
        if content_type:
            q += " AND content_type=?"
            params.append(content_type)
        q += " ORDER BY category, subject LIMIT 50"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Controle de Atualização ──────────────────────────────
    def get_last_update(self, update_type="videos"):
        """Retorna a data/hora da última atualização bem-sucedida."""
        conn = self._conn()
        row = conn.execute(
            """SELECT completed_at FROM update_log
               WHERE update_type=? AND status='success'
               ORDER BY completed_at DESC LIMIT 1""",
            (update_type,),
        ).fetchone()
        conn.close()
        if row and row["completed_at"]:
            try:
                return datetime.fromisoformat(row["completed_at"])
            except (ValueError, TypeError):
                return None
        return None

    def needs_update(self, update_type="videos", interval_hours=24):
        """Verifica se já passou o intervalo desde a última atualização."""
        last = self.get_last_update(update_type)
        if last is None:
            return True
        diff = datetime.now() - last
        return diff.total_seconds() >= interval_hours * 3600

    def log_update_start(self, update_type, category=None, subject=None):
        """Registra início de uma atualização."""
        conn = self._conn()
        conn.execute(
            """INSERT INTO update_log (update_type, category, subject, status)
               VALUES (?, ?, ?, 'running')""",
            (update_type, category, subject),
        )
        conn.commit()
        log_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return log_id

    def log_update_finish(self, log_id, status="success", videos_updated=0, error_message=None):
        """Registra fim de uma atualização."""
        conn = self._conn()
        conn.execute(
            """UPDATE update_log
               SET status=?, videos_updated=?, error_message=?, completed_at=?
               WHERE id=?""",
            (status, videos_updated, error_message,
             datetime.now().isoformat(), log_id),
        )
        conn.commit()
        conn.close()

    def get_update_history(self, limit=20):
        """Retorna histórico de atualizações."""
        conn = self._conn()
        rows = conn.execute(
            """SELECT * FROM update_log
               ORDER BY started_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── CRUD de vídeos (para o atualizador) ──────────────────
    def upsert_video(self, category, subject, topic, url, title, channel):
        """Insere ou atualiza um vídeo no banco."""
        conn = self._conn()
        existing = conn.execute(
            """SELECT id FROM content
               WHERE category=? AND subject=? AND topic=?
                     AND content_type='video' AND video_url=?""",
            (category, subject, topic, url),
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE content SET video_title=?, video_channel=?, updated_at=?
                   WHERE id=?""",
                (title, channel, datetime.now().isoformat(), existing["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO content
                   (category, subject, topic, video_url, video_title, video_channel,
                    content_type, updated_at)
                   VALUES (?,?,?,?,?,?,'video',?)""",
                (category, subject, topic, url, title, channel,
                 datetime.now().isoformat()),
            )
        conn.commit()
        conn.close()

    def replace_videos_for_topic(self, category, subject, topic, new_videos):
        """Remove vídeos antigos de um tópico e insere os novos."""
        conn = self._conn()
        conn.execute(
            """DELETE FROM content
               WHERE category=? AND subject=? AND topic=? AND content_type='video'""",
            (category, subject, topic),
        )
        for v in new_videos:
            conn.execute(
                """INSERT INTO content
                   (category, subject, topic, video_url, video_title, video_channel,
                    content_type, updated_at)
                   VALUES (?,?,?,?,?,?,'video',?)""",
                (category, subject, topic, v["url"], v["title"], v["channel"],
                 datetime.now().isoformat()),
            )
        conn.commit()
        conn.close()
        return len(new_videos)

    def get_all_video_topics(self):
        """Retorna todos os (category, subject, topic) que possuem vídeos."""
        conn = self._conn()
        rows = conn.execute(
            """SELECT DISTINCT category, subject, topic
               FROM content WHERE content_type='video'
               ORDER BY category, subject, topic"""
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Questões Reais do ENEM (Cache) ───────────────────────
    def cache_enem_questions(self, questions: list[dict]) -> int:
        """Salva questões do ENEM no cache local. Retorna quantas foram inseridas."""
        conn = self._conn()
        inserted = 0
        for q in questions:
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO enem_questions
                       (year, question_index, title, discipline, discipline_name,
                        language, context, question_intro, question_text,
                        options, correct_answer, correct_letter, images, alt_images)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        q["year"], q["index"], q.get("title", ""),
                        q.get("discipline", ""), q.get("discipline_name", ""),
                        q.get("language"), q.get("context", ""),
                        q.get("question_intro", ""), q["question_text"],
                        json.dumps(q["options"], ensure_ascii=False),
                        q["correct_answer"], q.get("correct_letter", ""),
                        json.dumps(q.get("images", []), ensure_ascii=False),
                        json.dumps(q.get("alt_images", []),
                                   ensure_ascii=False),
                    ),
                )
                inserted += 1
            except Exception:
                continue
        conn.commit()
        conn.close()
        return inserted

    def get_cached_enem_years(self) -> list[int]:
        """Retorna os anos que já têm questões em cache."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT DISTINCT year FROM enem_questions ORDER BY year DESC"
        ).fetchall()
        conn.close()
        return [r["year"] for r in rows]

    def get_cached_enem_year_count(self, year: int) -> int:
        """Retorna quantas questões estão em cache para um ano."""
        conn = self._conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM enem_questions WHERE year=?", (year,)
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0

    def get_enem_disciplines_for_year(self, year: int) -> list[dict]:
        """Retorna disciplinas disponíveis para um ano com contagem de questões."""
        conn = self._conn()
        rows = conn.execute(
            """SELECT discipline, discipline_name, COUNT(*) as count
               FROM enem_questions
               WHERE year=? AND discipline != ''
               GROUP BY discipline
               ORDER BY discipline_name""",
            (year,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_enem_questions(
        self, year: int, discipline: str = None,
        limit: int = 45, randomize: bool = True
    ) -> list[dict]:
        """Retorna questões do ENEM do cache por ano e disciplina."""
        conn = self._conn()
        q = "SELECT * FROM enem_questions WHERE year=?"
        params: list = [year]
        if discipline:
            q += " AND discipline=?"
            params.append(discipline)
        if randomize:
            q += " ORDER BY RANDOM()"
        else:
            q += " ORDER BY question_index"
        q += " LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            d["options"] = json.loads(d["options"])
            d["images"] = json.loads(d.get("images") or "[]")
            d["alt_images"] = json.loads(d.get("alt_images") or "[]")
            result.append(d)
        return result

    def has_enem_year_cached(self, year: int) -> bool:
        """Verifica se um ano já tem questões em cache."""
        return self.get_cached_enem_year_count(year) > 0

    # ── Progresso do Quiz ENEM Real ──────────────────────────
    def save_enem_quiz_progress(
        self, year: int, discipline: str, total: int,
        correct: int, score: float, user_id: int = None
    ):
        """Salva resultado de um quiz de questões reais do ENEM."""
        conn = self._conn()
        conn.execute(
            """INSERT INTO enem_quiz_progress
               (user_id, year, discipline, total_questions, correct_answers, score)
               VALUES (?,?,?,?,?,?)""",
            (user_id, year, discipline, total, correct, score),
        )
        conn.commit()
        conn.close()

    def get_enem_quiz_history(self, user_id: int = None, limit: int = 50) -> list[dict]:
        """Retorna histórico de quizzes ENEM reais do usuário."""
        conn = self._conn()
        rows = conn.execute(
            """SELECT * FROM enem_quiz_progress
               WHERE user_id IS ?
               ORDER BY completed_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_enem_quiz_stats_by_year(self, user_id: int = None) -> list[dict]:
        """Retorna estatísticas agrupadas por ano."""
        conn = self._conn()
        rows = conn.execute(
            """SELECT year, discipline,
                      COUNT(*) as attempts,
                      AVG(score) as avg_score,
                      MAX(score) as best_score,
                      SUM(total_questions) as total_q,
                      SUM(correct_answers) as total_correct
               FROM enem_quiz_progress
               WHERE user_id IS ?
               GROUP BY year, discipline
               ORDER BY year DESC""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════════════
    # ── GAMIFICAÇÃO — XP, Níveis, Conquistas ─────────────────
    # ══════════════════════════════════════════════════════════

    XP_PER_LEVEL = 100  # XP necessário por nível (scaling)

    def xp_for_level(self, level: int) -> int:
        """XP total necessário para alcançar um nível."""
        return int(self.XP_PER_LEVEL * level * 1.2)

    def add_xp(self, user_id: int, amount: int, source: str, description: str = "") -> dict:
        """Adiciona XP ao usuário. Retorna {"new_xp", "new_level", "leveled_up", "achievements"}."""
        if not user_id or amount <= 0:
            return {"new_xp": 0, "new_level": 1, "leveled_up": False, "achievements": []}

        conn = self._conn()
        user = conn.execute(
            "SELECT xp, level FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            conn.close()
            return {"new_xp": 0, "new_level": 1, "leveled_up": False, "achievements": []}

        old_level = user["level"] or 1
        new_xp = (user["xp"] or 0) + amount

        # Calcular novo nível
        new_level = old_level
        while new_xp >= self.xp_for_level(new_level + 1):
            new_level += 1

        conn.execute("UPDATE users SET xp=?, level=? WHERE id=?",
                     (new_xp, new_level, user_id))
        conn.execute(
            "INSERT INTO xp_log (user_id, amount, source, description) VALUES (?,?,?,?)",
            (user_id, amount, source, description),
        )
        conn.commit()
        conn.close()

        # Verificar conquistas de nível
        new_achievements = []
        if new_level > old_level:
            level_achievements = self._check_level_achievements(
                user_id, new_level)
            new_achievements.extend(level_achievements)

        return {
            "new_xp": new_xp,
            "new_level": new_level,
            "leveled_up": new_level > old_level,
            "achievements": new_achievements,
        }

    def get_xp_info(self, user_id: int) -> dict:
        """Retorna informações de XP do usuário."""
        if not user_id:
            return {"xp": 0, "level": 1, "xp_current_level": 0, "xp_next_level": 120, "progress": 0.0}
        conn = self._conn()
        user = conn.execute(
            "SELECT xp, level FROM users WHERE id=?", (user_id,)).fetchone()
        conn.close()
        if not user:
            return {"xp": 0, "level": 1, "xp_current_level": 0, "xp_next_level": 120, "progress": 0.0}

        xp = user["xp"] or 0
        level = user["level"] or 1
        xp_this = self.xp_for_level(level)
        xp_next = self.xp_for_level(level + 1)
        progress = (xp - xp_this) / (xp_next -
                                     xp_this) if (xp_next - xp_this) > 0 else 0.0
        return {
            "xp": xp, "level": level,
            "xp_current_level": xp_this, "xp_next_level": xp_next,
            "progress": min(max(progress, 0.0), 1.0),
        }

    def get_xp_today(self, user_id: int) -> int:
        """Retorna XP ganho hoje."""
        if not user_id:
            return 0
        conn = self._conn()
        row = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as total FROM xp_log WHERE user_id=? AND DATE(earned_at)=DATE('now','localtime')",
            (user_id,),
        ).fetchone()
        conn.close()
        return row["total"] if row else 0

    def update_streak(self, user_id: int) -> dict:
        """Atualiza streak do usuário. Chamar ao logar ou completar atividade."""
        if not user_id:
            return {"streak": 0, "is_new_day": False}
        conn = self._conn()
        user = conn.execute(
            "SELECT streak_days, last_active_date, longest_streak FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
        if not user:
            conn.close()
            return {"streak": 0, "is_new_day": False}

        today = datetime.now().strftime("%Y-%m-%d")
        last = user["last_active_date"]
        streak = user["streak_days"] or 0
        longest = user["longest_streak"] or 0

        if last == today:
            conn.close()
            return {"streak": streak, "is_new_day": False}

        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        if last == yesterday:
            streak += 1
        elif last is None or last != today:
            streak = 1

        if streak > longest:
            longest = streak

        conn.execute(
            "UPDATE users SET streak_days=?, last_active_date=?, longest_streak=? WHERE id=?",
            (streak, today, longest, user_id),
        )
        conn.commit()
        conn.close()

        # Verificar conquistas de streak
        self._check_streak_achievements(user_id, streak)

        return {"streak": streak, "is_new_day": True}

    def get_streak(self, user_id: int) -> dict:
        """Retorna informações de streak."""
        if not user_id:
            return {"streak": 0, "longest": 0, "last_active": None}
        conn = self._conn()
        user = conn.execute(
            "SELECT streak_days, longest_streak, last_active_date FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
        conn.close()
        if not user:
            return {"streak": 0, "longest": 0, "last_active": None}
        return {
            "streak": user["streak_days"] or 0,
            "longest": user["longest_streak"] or 0,
            "last_active": user["last_active_date"],
        }

    # ── Conquistas ───────────────────────────────────────────
    def get_all_achievements(self) -> list[dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM achievements ORDER BY category, requirement_value").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_user_achievements(self, user_id: int) -> list[dict]:
        if not user_id:
            return []
        conn = self._conn()
        rows = conn.execute(
            """SELECT a.*, ua.earned_at
               FROM user_achievements ua
               JOIN achievements a ON ua.achievement_id = a.id
               WHERE ua.user_id=?
               ORDER BY ua.earned_at DESC""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def grant_achievement(self, user_id: int, achievement_key: str) -> dict | None:
        """Concede uma conquista ao usuário. Retorna a conquista ou None se já tinha."""
        if not user_id:
            return None
        conn = self._conn()
        ach = conn.execute(
            "SELECT * FROM achievements WHERE key=?", (achievement_key,)).fetchone()
        if not ach:
            conn.close()
            return None
        try:
            conn.execute(
                "INSERT INTO user_achievements (user_id, achievement_id) VALUES (?,?)",
                (user_id, ach["id"]),
            )
            conn.commit()
            # Dar XP da conquista
            if ach["xp_reward"] > 0:
                self.add_xp(user_id, ach["xp_reward"],
                            "achievement", f"Conquista: {ach['title']}")
            conn.close()
            return dict(ach)
        except Exception:
            conn.close()
            return None

    def has_achievement(self, user_id: int, achievement_key: str) -> bool:
        if not user_id:
            return False
        conn = self._conn()
        row = conn.execute(
            """SELECT 1 FROM user_achievements ua
               JOIN achievements a ON ua.achievement_id=a.id
               WHERE ua.user_id=? AND a.key=?""",
            (user_id, achievement_key),
        ).fetchone()
        conn.close()
        return row is not None

    def check_and_grant_achievements(self, user_id: int) -> list[dict]:
        """Verifica e concede todas as conquistas pendentes."""
        if not user_id:
            return []
        earned = []
        stats = self._get_achievement_stats(user_id)
        all_achs = self.get_all_achievements()

        for ach in all_achs:
            if self.has_achievement(user_id, ach["key"]):
                continue
            req_type = ach.get("requirement_type", "")
            req_val = ach.get("requirement_value", 0)
            current = stats.get(req_type, 0)
            if current >= req_val:
                result = self.grant_achievement(user_id, ach["key"])
                if result:
                    earned.append(result)
        return earned

    def _get_achievement_stats(self, user_id: int) -> dict:
        """Coleta estatísticas para verificar conquistas."""
        conn = self._conn()
        s = {}

        # Pomodoros completados
        row = conn.execute(
            "SELECT COUNT(*) as c FROM pomodoro_sessions WHERE user_id=? AND session_type='foco'",
            (user_id,),
        ).fetchone()
        s["pomodoros_completed"] = row["c"] if row else 0

        # Pomodoros hoje
        row = conn.execute(
            "SELECT COUNT(*) as c FROM pomodoro_sessions WHERE user_id=? AND session_type='foco' AND DATE(completed_at)=DATE('now','localtime')",
            (user_id,),
        ).fetchone()
        s["daily_pomodoros"] = row["c"] if row else 0

        # Quizzes respondidos
        row = conn.execute(
            "SELECT COALESCE(SUM(total_questions),0) as c FROM study_progress WHERE user_id=?",
            (user_id,),
        ).fetchone()
        s["quizzes_completed"] = row["c"] if row else 0

        # Quiz perfeito
        row = conn.execute(
            "SELECT COUNT(*) as c FROM study_progress WHERE user_id=? AND score>=100",
            (user_id,),
        ).fetchone()
        s["perfect_score"] = row["c"] if row else 0

        # ENEM quizzes
        row = conn.execute(
            "SELECT COUNT(*) as c FROM enem_quiz_progress WHERE user_id=?",
            (user_id,),
        ).fetchone()
        s["enem_quizzes"] = row["c"] if row else 0

        # Streak
        user = conn.execute(
            "SELECT streak_days, level FROM users WHERE id=?", (user_id,),
        ).fetchone()
        s["streak_days"] = user["streak_days"] if user else 0
        s["level_reached"] = user["level"] if user else 1

        # Flashcards criados
        row = conn.execute(
            "SELECT COUNT(*) as c FROM flashcards WHERE user_id=?", (user_id,),
        ).fetchone()
        s["flashcards_created"] = row["c"] if row else 0

        # Flashcards revisados
        row = conn.execute(
            "SELECT COUNT(*) as c FROM flashcard_reviews WHERE user_id=?", (user_id,),
        ).fetchone()
        s["flashcards_reviewed"] = row["c"] if row else 0

        # Tarefas concluídas
        row = conn.execute(
            "SELECT COUNT(*) as c FROM tasks WHERE user_id=? AND status='concluída'",
            (user_id,),
        ).fetchone()
        s["tasks_completed"] = row["c"] if row else 0

        # Horas de foco
        row = conn.execute(
            "SELECT COALESCE(SUM(duration),0) as m FROM pomodoro_sessions WHERE user_id=? AND session_type='foco'",
            (user_id,),
        ).fetchone()
        s["focus_hours"] = (row["m"] if row else 0) / 60

        conn.close()
        return s

    def _check_level_achievements(self, user_id, level):
        earned = []
        mapping = {5: "level_5", 10: "level_10", 25: "level_25"}
        for lvl, key in mapping.items():
            if level >= lvl and not self.has_achievement(user_id, key):
                r = self.grant_achievement(user_id, key)
                if r:
                    earned.append(r)
        return earned

    def _check_streak_achievements(self, user_id, streak):
        mapping = {3: "streak_3", 7: "streak_7", 30: "streak_30"}
        for days, key in mapping.items():
            if streak >= days and not self.has_achievement(user_id, key):
                self.grant_achievement(user_id, key)

    # ══════════════════════════════════════════════════════════
    # ── FLASHCARDS ───────────────────────────────────────────
    # ══════════════════════════════════════════════════════════

    def create_flashcard(self, front, back, subject, topic="", category="enem",
                         difficulty="médio", user_id=None) -> int:
        conn = self._conn()
        conn.execute(
            """INSERT INTO flashcards (user_id, category, subject, topic, front, back, difficulty)
               VALUES (?,?,?,?,?,?,?)""",
            (user_id, category, subject, topic, front, back, difficulty),
        )
        conn.commit()
        fid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return fid

    def get_flashcards(self, user_id=None, category=None, subject=None) -> list[dict]:
        conn = self._conn()
        q = "SELECT * FROM flashcards WHERE (user_id IS ? OR user_id IS NULL)"
        params: list = [user_id]
        if category:
            q += " AND category=?"
            params.append(category)
        if subject:
            q += " AND subject=?"
            params.append(subject)
        q += " ORDER BY subject, topic"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_flashcards_for_review(self, user_id=None, limit=20) -> list[dict]:
        """Retorna flashcards que precisam ser revisados (repetição espaçada)."""
        conn = self._conn()
        # Cards nunca revisados ou com revisão vencida
        rows = conn.execute(
            """SELECT f.*, fr.easiness, fr.interval, fr.repetitions, fr.next_review
               FROM flashcards f
               LEFT JOIN (
                   SELECT flashcard_id, easiness, interval, repetitions, next_review,
                          ROW_NUMBER() OVER (PARTITION BY flashcard_id ORDER BY reviewed_at DESC) as rn
                   FROM flashcard_reviews WHERE user_id IS ?
               ) fr ON f.id = fr.flashcard_id AND fr.rn = 1
               WHERE (f.user_id IS ? OR f.user_id IS NULL)
                 AND (fr.next_review IS NULL OR fr.next_review <= datetime('now','localtime'))
               ORDER BY CASE WHEN fr.next_review IS NULL THEN 0 ELSE 1 END, fr.next_review
               LIMIT ?""",
            (user_id, user_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_flashcard_review(self, flashcard_id: int, quality: int, user_id=None) -> dict:
        """
        Salva revisão de flashcard usando algoritmo SM-2.
        quality: 0-5 (0=esqueceu, 5=perfeito)
        Retorna {"easiness", "interval", "next_review"}.
        """
        conn = self._conn()
        # Buscar estado anterior
        prev = conn.execute(
            """SELECT easiness, interval, repetitions FROM flashcard_reviews
               WHERE flashcard_id=? AND user_id IS ?
               ORDER BY reviewed_at DESC LIMIT 1""",
            (flashcard_id, user_id),
        ).fetchone()

        if prev:
            easiness = prev["easiness"]
            interval = prev["interval"]
            reps = prev["repetitions"]
        else:
            easiness = 2.5
            interval = 1
            reps = 0

        # Algoritmo SM-2
        if quality >= 3:
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 6
            else:
                interval = int(interval * easiness)
            reps += 1
        else:
            reps = 0
            interval = 1

        easiness = max(1.3, easiness + 0.1 - (5 - quality)
                       * (0.08 + (5 - quality) * 0.02))

        next_review = (
            datetime.now() + __import__('datetime').timedelta(days=interval)).isoformat()

        conn.execute(
            """INSERT INTO flashcard_reviews
               (user_id, flashcard_id, quality, easiness, interval, repetitions, next_review)
               VALUES (?,?,?,?,?,?,?)""",
            (user_id, flashcard_id, quality, easiness, interval, reps, next_review),
        )
        conn.commit()
        conn.close()
        return {"easiness": easiness, "interval": interval, "next_review": next_review}

    def delete_flashcard(self, flashcard_id: int):
        conn = self._conn()
        conn.execute(
            "DELETE FROM flashcard_reviews WHERE flashcard_id=?", (flashcard_id,))
        conn.execute("DELETE FROM flashcards WHERE id=?", (flashcard_id,))
        conn.commit()
        conn.close()

    def delete_all_flashcards(self, user_id=None):
        """Remove todos os flashcards e suas revisões do usuário."""
        conn = self._conn()
        # Pegar IDs dos flashcards do usuário
        rows = conn.execute(
            "SELECT id FROM flashcards WHERE (user_id IS ? OR user_id IS NULL)",
            (user_id,),
        ).fetchall()
        ids = [r["id"] for r in rows]
        if ids:
            placeholders = ",".join("?" * len(ids))
            conn.execute(
                f"DELETE FROM flashcard_reviews WHERE flashcard_id IN ({placeholders})", ids)
            conn.execute(
                f"DELETE FROM flashcards WHERE id IN ({placeholders})", ids)
        conn.commit()
        conn.close()
        return len(ids)

    def get_flashcard_subjects(self, user_id=None) -> list[str]:
        conn = self._conn()
        rows = conn.execute(
            """SELECT DISTINCT subject FROM flashcards
               WHERE (user_id IS ? OR user_id IS NULL)
               ORDER BY subject""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [r["subject"] for r in rows]

    def get_flashcard_stats(self, user_id=None) -> dict:
        conn = self._conn()
        total = conn.execute(
            "SELECT COUNT(*) as c FROM flashcards WHERE (user_id IS ? OR user_id IS NULL)",
            (user_id,),
        ).fetchone()["c"]
        reviewed = conn.execute(
            "SELECT COUNT(DISTINCT flashcard_id) as c FROM flashcard_reviews WHERE user_id IS ?",
            (user_id,),
        ).fetchone()["c"]
        due = conn.execute(
            """SELECT COUNT(*) as c FROM flashcards f
               LEFT JOIN (
                   SELECT flashcard_id, next_review,
                          ROW_NUMBER() OVER (PARTITION BY flashcard_id ORDER BY reviewed_at DESC) as rn
                   FROM flashcard_reviews WHERE user_id IS ?
               ) fr ON f.id=fr.flashcard_id AND fr.rn=1
               WHERE (f.user_id IS ? OR f.user_id IS NULL)
                 AND (fr.next_review IS NULL OR fr.next_review <= datetime('now','localtime'))""",
            (user_id, user_id),
        ).fetchone()["c"]
        conn.close()
        return {"total": total, "reviewed": reviewed, "due": due}

    # ══════════════════════════════════════════════════════════
    # ── METAS DIÁRIAS ────────────────────────────────────────
    # ══════════════════════════════════════════════════════════

    def get_or_create_daily_goals(self, user_id: int) -> list[dict]:
        """Retorna metas do dia, criando se não existirem."""
        if not user_id:
            return []
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._conn()

        goals = conn.execute(
            "SELECT * FROM daily_goals WHERE user_id=? AND date=?",
            (user_id, today),
        ).fetchall()

        if not goals:
            user = conn.execute(
                "SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            default_goals = [
                ("pomodoro", user["daily_pomodoro_goal"] if user else 4),
                ("xp", user["daily_xp_goal"] if user else 100),
                ("quiz", user["daily_quiz_goal"] if user else 10),
            ]
            for gtype, target in default_goals:
                conn.execute(
                    "INSERT INTO daily_goals (user_id, goal_type, target_value, date) VALUES (?,?,?,?)",
                    (user_id, gtype, target, today),
                )
            conn.commit()
            goals = conn.execute(
                "SELECT * FROM daily_goals WHERE user_id=? AND date=?",
                (user_id, today),
            ).fetchall()

        conn.close()
        return [dict(g) for g in goals]

    def update_daily_goal_progress(self, user_id: int, goal_type: str, increment: int = 1):
        """Incrementa o progresso de uma meta diária."""
        if not user_id:
            return
        today = datetime.now().strftime("%Y-%m-%d")
        self.get_or_create_daily_goals(user_id)  # garantir que existe
        conn = self._conn()
        conn.execute(
            """UPDATE daily_goals SET current_value = current_value + ?,
               completed = CASE WHEN current_value + ? >= target_value THEN 1 ELSE 0 END
               WHERE user_id=? AND goal_type=? AND date=?""",
            (increment, increment, user_id, goal_type, today),
        )
        conn.commit()
        conn.close()

    def get_daily_goals_summary(self, user_id: int) -> dict:
        """Resumo rápido das metas de hoje."""
        goals = self.get_or_create_daily_goals(user_id)
        completed = sum(1 for g in goals if g["completed"])
        return {
            "goals": goals,
            "total": len(goals),
            "completed": completed,
            "all_done": completed == len(goals),
        }

    def get_today_stats(self, user_id: int) -> dict:
        """Estatísticas de hoje para o dashboard."""
        if not user_id:
            return {"pomodoros": 0, "focus_min": 0, "questions": 0, "xp_today": 0}
        conn = self._conn()
        pom = conn.execute(
            "SELECT COUNT(*) as c, COALESCE(SUM(duration),0) as m FROM pomodoro_sessions WHERE user_id=? AND session_type='foco' AND DATE(completed_at)=DATE('now','localtime')",
            (user_id,),
        ).fetchone()
        quiz = conn.execute(
            "SELECT COALESCE(SUM(total_questions),0) as c FROM study_progress WHERE user_id=? AND DATE(completed_at)=DATE('now','localtime')",
            (user_id,),
        ).fetchone()
        conn.close()
        return {
            "pomodoros": pom["c"] if pom else 0,
            "focus_min": pom["m"] if pom else 0,
            "questions": quiz["c"] if quiz else 0,
            "xp_today": self.get_xp_today(user_id),
        }

    # ══════════════════════════════════════════════════════════
    # ── TEORIA / EDITAIS ───────────────────────────────────────
    # ══════════════════════════════════════════════════════════
    def mark_theory_read(self, user_id: int, area: str, topic_title: str,
                         completed: bool = True, notes: str = None):
        """Marca um tópico teórico como lido/concluído."""
        if not user_id:
            return
        conn = self._conn()
        conn.execute("""
            INSERT INTO theory_progress (user_id, area, topic_title, completed, notes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, area, topic_title)
            DO UPDATE SET completed=?, notes=COALESCE(?, notes), read_at=CURRENT_TIMESTAMP
        """, (user_id, area, topic_title, int(completed), notes,
              int(completed), notes))
        conn.commit()
        conn.close()

        # XP por estudar teoria
        if completed:
            self.add_xp(user_id, 15, "teoria", f"Estudou: {topic_title}")
            self.update_daily_goal_progress(user_id, "teoria")

    def get_theory_progress(self, user_id: int) -> dict:
        """Retorna progresso de teoria: {(area, topic_title): {completed, read_at, notes}}."""
        if not user_id:
            return {}
        conn = self._conn()
        rows = conn.execute(
            "SELECT area, topic_title, completed, read_at, notes FROM theory_progress WHERE user_id=?",
            (user_id,),
        ).fetchall()
        conn.close()
        return {
            (r["area"], r["topic_title"]): {
                "completed": bool(r["completed"]),
                "read_at": r["read_at"],
                "notes": r["notes"],
            }
            for r in rows
        }

    def get_theory_stats(self, user_id: int) -> dict:
        """Retorna estatísticas de progresso de teoria por área."""
        if not user_id:
            return {}
        conn = self._conn()
        rows = conn.execute("""
            SELECT area, COUNT(*) as read_count,
                   SUM(CASE WHEN completed=1 THEN 1 ELSE 0 END) as completed_count
            FROM theory_progress WHERE user_id=?
            GROUP BY area
        """, (user_id,)).fetchall()
        conn.close()
        return {
            r["area"]: {"read": r["read_count"],
                        "completed": r["completed_count"]}
            for r in rows
        }

    # ══════════════════════════════════════════════════════════
    # ── NOVOS MÉTODOS — Settings / Perfil ────────────────────
    # ══════════════════════════════════════════════════════════
    def update_user_goals(self, user_id: int, pomodoro: int, xp: int, quiz: int):
        """Atualiza as metas diárias do usuário."""
        conn = self._conn()
        conn.execute(
            "UPDATE users SET daily_pomodoro_goal=?, daily_xp_goal=?, daily_quiz_goal=? WHERE id=?",
            (pomodoro, xp, quiz, user_id),
        )
        conn.commit()
        conn.close()

    def update_user_display_name(self, user_id: int, new_name: str):
        """Atualiza o nome de exibição do usuário."""
        conn = self._conn()
        conn.execute(
            "UPDATE users SET display_name=? WHERE id=?",
            (new_name, user_id),
        )
        conn.commit()
        conn.close()

    def update_user_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Altera a senha do usuário. Retorna True se sucesso, False se senha antiga incorreta."""
        conn = self._conn()
        try:
            user = conn.execute(
                "SELECT password_hash FROM users WHERE id=?", (user_id,)
            ).fetchone()
            if not user or not self._verify_password(old_password, user["password_hash"]):
                return False

            conn.execute(
                "UPDATE users SET password_hash=? WHERE id=?",
                (self._hash(new_password), user_id),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def clear_pomodoro_sessions(self, user_id: int):
        """Remove todas as sessões Pomodoro de um usuário."""
        conn = self._conn()
        conn.execute(
            "DELETE FROM pomodoro_sessions WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
