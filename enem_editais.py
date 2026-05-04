"""
Editais do ENEM — Todos os anos (1998 – 2025) com tema da redação.

Fonte: INEP / MEC — histórico oficial das edições do ENEM.
"""

ENEM_EDITIONS = [
    {
        "year": 1998,
        "edition": "1ª edição",
        "tema_redacao": "Viver e aprender",
        "data_prova": "30 de agosto de 1998",
        "inscritos": "157.221",
        "nota_maxima_redacao": "100 (escala antiga)",
        "detalhes": (
            "Primeira edição do ENEM. Criado para avaliar o desempenho dos "
            "estudantes ao final da educação básica. Prova com 63 questões "
            "objetivas e 1 redação. A nota ia de 0 a 100."
        ),
    },
    {
        "year": 1999,
        "edition": "2ª edição",
        "tema_redacao": "Cidadania e participação social",
        "data_prova": "29 de agosto de 1999",
        "inscritos": "346.953",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Segundo ano do exame, com aumento significativo de inscritos. "
            "Manteve o formato de 63 questões e redação dissertativa."
        ),
    },
    {
        "year": 2000,
        "edition": "3ª edição",
        "tema_redacao": "Direitos da criança e do adolescente: como enfrentar esse desafio nacional?",
        "data_prova": "27 de agosto de 2000",
        "inscritos": "390.180",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Terceira edição do ENEM com temática social voltada para "
            "políticas públicas da juventude brasileira."
        ),
    },
    {
        "year": 2001,
        "edition": "4ª edição",
        "tema_redacao": "Desenvolvimento e preservação ambiental: como conciliar os interesses em conflito?",
        "data_prova": "26 de agosto de 2001",
        "inscritos": "1.624.131",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Grande salto no número de inscritos. Tema ambiental marcou a "
            "prova, abordando desenvolvimento sustentável."
        ),
    },
    {
        "year": 2002,
        "edition": "5ª edição",
        "tema_redacao": "O direito de votar: como fazer dessa conquista um instrumento a serviço da democracia?",
        "data_prova": "25 de agosto de 2002",
        "inscritos": "1.829.170",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Em ano eleitoral, o tema abordou cidadania e participação "
            "democrática através do voto."
        ),
    },
    {
        "year": 2003,
        "edition": "6ª edição",
        "tema_redacao": "A violência na sociedade brasileira: como mudar as regras desse jogo?",
        "data_prova": "31 de agosto de 2003",
        "inscritos": "1.882.393",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Tema sobre violência urbana, abordando causas e possíveis "
            "soluções para a realidade brasileira."
        ),
    },
    {
        "year": 2004,
        "edition": "7ª edição",
        "tema_redacao": "Como garantir a liberdade de informação e evitar abusos nos meios de comunicação?",
        "data_prova": "29 de agosto de 2004",
        "inscritos": "1.552.316",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Tema sobre mídia e liberdade de imprensa, discutindo os "
            "limites entre informação e privacidade."
        ),
    },
    {
        "year": 2005,
        "edition": "8ª edição",
        "tema_redacao": "O trabalho infantil na realidade brasileira",
        "data_prova": "28 de agosto de 2005",
        "inscritos": "3.004.491",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Número de inscritos triplicou. Tema abordou a exploração do "
            "trabalho infantil e suas consequências sociais."
        ),
    },
    {
        "year": 2006,
        "edition": "9ª edição",
        "tema_redacao": "O poder de transformação da leitura",
        "data_prova": "27 de agosto de 2006",
        "inscritos": "3.742.827",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Tema sobre a importância da leitura como instrumento de "
            "transformação individual e social."
        ),
    },
    {
        "year": 2007,
        "edition": "10ª edição",
        "tema_redacao": "O desafio de se conviver com a diferença",
        "data_prova": "26 de agosto de 2007",
        "inscritos": "3.568.592",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Décima edição do ENEM. Tema sobre diversidade e tolerância "
            "na sociedade brasileira."
        ),
    },
    {
        "year": 2008,
        "edition": "11ª edição",
        "tema_redacao": "Como preservar a floresta Amazônica: educação ambiental e fiscalização",
        "data_prova": "31 de agosto de 2008",
        "inscritos": "4.018.050",
        "nota_maxima_redacao": "100",
        "detalhes": (
            "Último ano do ENEM no formato antigo (63 questões). "
            "Tema sobre preservação ambiental da Amazônia."
        ),
    },
    {
        "year": 2009,
        "edition": "12ª edição — Novo ENEM",
        "tema_redacao": "O indivíduo frente à ética nacional",
        "data_prova": "5 e 6 de dezembro de 2009",
        "inscritos": "4.148.721",
        "nota_maxima_redacao": "1000 (nova escala)",
        "detalhes": (
            "NOVO ENEM: Reformulação completa. Passa a ter 180 questões "
            "(45 por área) + redação, aplicado em 2 dias. Adota a TRI "
            "(Teoria de Resposta ao Item). Nota de 0 a 1000. Começa a "
            "ser usado para ingresso em universidades via SiSU."
        ),
    },
    {
        "year": 2010,
        "edition": "13ª edição",
        "tema_redacao": "O trabalho na construção da dignidade humana",
        "data_prova": "6 e 7 de novembro de 2010",
        "inscritos": "4.626.094",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre a valorização do trabalho e sua relação com "
            "a dignidade humana. SiSU consolidado como forma de ingresso."
        ),
    },
    {
        "year": 2011,
        "edition": "14ª edição",
        "tema_redacao": "Viver em rede no século XXI: os limites entre o público e o privado",
        "data_prova": "22 e 23 de outubro de 2011",
        "inscritos": "5.380.857",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre redes sociais e privacidade digital, refletindo "
            "a expansão da internet no Brasil."
        ),
    },
    {
        "year": 2012,
        "edition": "15ª edição",
        "tema_redacao": "O movimento imigratório para o Brasil no século XXI",
        "data_prova": "3 e 4 de novembro de 2012",
        "inscritos": "5.791.332",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre imigração contemporânea no Brasil. "
            "Maior número de inscritos até então."
        ),
    },
    {
        "year": 2013,
        "edition": "16ª edição",
        "tema_redacao": "Efeitos da implantação da Lei Seca no Brasil",
        "data_prova": "26 e 27 de outubro de 2013",
        "inscritos": "7.173.574",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Recorde de inscritos (mais de 7 milhões). Tema sobre "
            "trânsito e a Lei Seca como política pública."
        ),
    },
    {
        "year": 2014,
        "edition": "17ª edição",
        "tema_redacao": "Publicidade infantil em questão no Brasil",
        "data_prova": "8 e 9 de novembro de 2014",
        "inscritos": "8.722.290",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Novo recorde com quase 9 milhões de inscritos. "
            "Tema sobre os efeitos da publicidade voltada para crianças."
        ),
    },
    {
        "year": 2015,
        "edition": "18ª edição",
        "tema_redacao": "A persistência da violência contra a mulher na sociedade brasileira",
        "data_prova": "24 e 25 de outubro de 2015",
        "inscritos": "7.746.057",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre violência de gênero e a Lei Maria da Penha. "
            "Considerado um dos temas mais impactantes da história do ENEM."
        ),
    },
    {
        "year": 2016,
        "edition": "19ª edição",
        "tema_redacao": "Caminhos para combater a intolerância religiosa no Brasil",
        "data_prova": "5 e 6 de novembro de 2016",
        "inscritos": "8.627.367",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre liberdade religiosa e laicidade do Estado. "
            "Houve 1ª aplicação em dois domingos (ocupação de escolas)."
        ),
    },
    {
        "year": 2017,
        "edition": "20ª edição",
        "tema_redacao": "Desafios para a formação educacional de surdos no Brasil",
        "data_prova": "5 e 12 de novembro de 2017",
        "inscritos": "6.731.341",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre inclusão educacional de pessoas surdas. "
            "Prova aplicada em dois domingos alternados."
        ),
    },
    {
        "year": 2018,
        "edition": "21ª edição",
        "tema_redacao": "Manipulação do comportamento do usuário pelo controle de dados na internet",
        "data_prova": "4 e 11 de novembro de 2018",
        "inscritos": "5.513.662",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre proteção de dados e privacidade digital, "
            "em contexto de debates sobre LGPD e fake news."
        ),
    },
    {
        "year": 2019,
        "edition": "22ª edição",
        "tema_redacao": "Democratização do acesso ao cinema no Brasil",
        "data_prova": "3 e 10 de novembro de 2019",
        "inscritos": "5.095.308",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre acesso à cultura e ao cinema. Primeiro ENEM "
            "aplicado no formato digital (projeto piloto em 4 capitais)."
        ),
    },
    {
        "year": 2020,
        "edition": "23ª edição (adiado pela pandemia)",
        "tema_redacao": "O estigma associado às doenças mentais na sociedade brasileira",
        "data_prova": "17 e 24 de janeiro de 2021",
        "inscritos": "5.783.357",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "ENEM 2020 foi adiado devido à pandemia de COVID-19. "
            "Tema sobre saúde mental e estigma social, extremamente "
            "relevante no contexto pandêmico."
        ),
    },
    {
        "year": 2021,
        "edition": "24ª edição",
        "tema_redacao": "Invisibilidade e registro civil: garantia de acesso à cidadania no Brasil",
        "data_prova": "21 e 28 de novembro de 2021",
        "inscritos": "3.389.832",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre sub-registro e invisibilidade civil. "
            "Menor número de inscritos em anos, reflexo da pandemia."
        ),
    },
    {
        "year": 2022,
        "edition": "25ª edição",
        "tema_redacao": "Desafios para a valorização de comunidades e povos tradicionais no Brasil",
        "data_prova": "13 e 20 de novembro de 2022",
        "inscritos": "3.396.632",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre comunidades tradicionais (quilombolas, indígenas, "
            "ribeirinhos). Inscrições voltaram a crescer levemente."
        ),
    },
    {
        "year": 2023,
        "edition": "26ª edição",
        "tema_redacao": "Desafios para o enfrentamento da invisibilidade do trabalho de cuidado realizado pela mulher no Brasil",
        "data_prova": "5 e 12 de novembro de 2023",
        "inscritos": "3.933.848",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre a invisibilidade do trabalho doméstico e de "
            "cuidado feminino. Retomada do crescimento de inscritos."
        ),
    },
    {
        "year": 2024,
        "edition": "27ª edição",
        "tema_redacao": "Desafios para a valorização da herança africana no Brasil",
        "data_prova": "3 e 10 de novembro de 2024",
        "inscritos": "4.325.960",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Tema sobre a valorização da cultura e herança africana "
            "na formação da identidade brasileira. Número de inscritos "
            "continuou em recuperação."
        ),
    },
    {
        "year": 2025,
        "edition": "28ª edição",
        "tema_redacao": "Aguardando realização — edital previsto para maio de 2025",
        "data_prova": "Previsto para novembro de 2025",
        "inscritos": "Inscrições a abrir",
        "nota_maxima_redacao": "1000",
        "detalhes": (
            "Edição ainda não realizada. O edital com as datas, local de "
            "prova e regras será publicado pelo INEP no primeiro semestre "
            "de 2025. Fique atento ao site oficial do INEP."
        ),
    },
]


# ── Dados resumidos para consultas rápidas ───────────────────
ENEM_THEMES_BY_YEAR = {e["year"]: e["tema_redacao"] for e in ENEM_EDITIONS}

ENEM_YEARS = sorted([e["year"] for e in ENEM_EDITIONS])

# Estatísticas rápidas
ENEM_STATS = {
    "total_editions": len(ENEM_EDITIONS),
    "first_year": 1998,
    "last_year": 2025,
    "format_change_year": 2009,  # Novo ENEM
    "record_inscritos": {"year": 2014, "count": "8.722.290"},
}
