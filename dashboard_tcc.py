"""
Análise de Fricção em Data Parsing: Evidências Estatísticas do Fórum CorText
TCC - Universidade Federal da Bahia (UFBA)
"""

import json
import re
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Análise de Fricção em Data Parsing: Evidências Estatísticas do Fórum CorText | TCC UFBA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS
st.markdown("""
<style>
    /* Oculta sidebar */
    [data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    .main { background-color: #0e1117; }
    .kpi-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.5);
    }
    .kpi-title {
        color: #94a3b8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #38bdf8;
        margin-top: 6px;
    }
    .tcc-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .quote-box {
        background: rgba(30, 41, 59, 0.4);
        border-left: 4px solid #3b82f6;
        padding: 14px 18px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 16px;
    }
    .note-box {
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.25);
        padding: 14px 18px;
        border-radius: 8px;
        margin: 12px 0 20px 0;
        font-size: 0.88rem;
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)


# Carregamento e tratamento dos dados
DATA_JSON_PATH = os.path.join("output_forum", "forum_topics_full.json")
SUMMARY_JSON_PATH = os.path.join("output_forum", "resumo_estatistico.json")


@st.cache_data
def load_data():
    if not os.path.exists(DATA_JSON_PATH):
        st.error(f"Arquivo não encontrado: {DATA_JSON_PATH}. Execute primeiro a extração via extract_forum.py.")
        return pd.DataFrame(), {}

    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        raw_topics = json.load(f)

    summary = {}
    if os.path.exists(SUMMARY_JSON_PATH):
        with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
            summary = json.load(f)

    df = pd.DataFrame(raw_topics)

    # Normalização de categorias
    df["category"] = df["category"].fillna("Sem Categoria").astype(str).str.strip()
    df["category"] = df["category"].apply(lambda c: c if c else "Sem Categoria")

    # Tratamento de datas
    df["date_published_dt"] = pd.to_datetime(df["date_published"], errors="coerce")
    df["year"] = df["date_published_dt"].dt.year
    df["year_str"] = df["year"].fillna("Desconhecido").astype(str).str.replace(".0", "", regex=False)

    # Detecção de formatos de entrada
    format_regexes = {
        "CSV": r"\b(csv|comma|semicolon|delimiter|separat)\b",
        "ZIP": r"\b(zip|archive|compress)\b",
        "Web of Science (WOS)": r"\b(wos|web of science)\b",
        "Scopus": r"\b(scopus)\b",
        "RIS": r"\b(ris)\b",
        "ISI": r"\b(isi)\b",
        "Factiva": r"\b(factiva)\b",
        "Excel / XLSX": r"\b(excel|xlsx|xls)\b",
        "PubMed": r"\b(pubmed|mesh)\b",
        "PDF": r"\b(pdf)\b",
        "TSV": r"\b(tsv)\b",
        "TXT": r"\b(txt|text file)\b",
        "Istex / Cairn": r"\b(istex|cairn)\b",
        "ProQuest": r"\b(proquest)\b"
    }

    def detect_formats(row):
        text = f"{row.get('title', '')} {row.get('question_body', '')}".lower()
        found = [fmt for fmt, pattern in format_regexes.items() if re.search(pattern, text)]
        return found

    df["detected_formats"] = df.apply(detect_formats, axis=1)
    df["has_heterogeneous_format"] = df["detected_formats"].apply(lambda x: len(x) > 0)

    # Padrões de mensagens de erro e falhas
    opacity_patterns = [
        r"no logs? found",
        r"no info in logs?",
        r"error",
        r"failed",
        r"erreur",
        r"empty",
        r"job id",
        r"acting weird",
        r"impossible",
        r"bloqu"
    ]
    opacity_regex = re.compile("|".join(opacity_patterns), re.IGNORECASE)

    def detect_opacity(row):
        text = f"{row.get('title', '')} {row.get('question_body', '')}"
        return bool(opacity_regex.search(text))

    df["has_opacity_symptom"] = df.apply(detect_opacity, axis=1)

    # Classificação de tópicos diretos e derivados de data parsing
    parsing_kw = [
        'pars', 'parser', 'parsing', 'upload', 'delimiter', 'encoding', 'utf-8', 
        'corpus terms indexer', 'corpus list indexer', 'corps terms indexer', 
        'importing', 'subcorpus', 'sub-corpus'
    ]
    derived_symptoms = [
        'network you produced is empty', 'reseau vide', 'network is empty', 'empty network',
        'no logs found', 'no info in logs', 'job id:'
    ]

    def classify_parsing(row):
        cat = row.get("category") or "Sem Categoria"
        title = (row.get("title") or "").lower()
        body = (row.get("question_body") or "").lower()
        full = f"{title} {body}"

        # 1. Categoria oficial Data processing
        if cat == "Data processing":
            return True, "Direto (Data processing)", "Falha Direta em Ingestão/Parsing"

        # 2. Menção a parsing, indexação ou delimitadores
        if any(k in full for k in parsing_kw):
            return True, "Derivado (Indexação/Parsing em Outra Etapa)", f"Parsing/Corpus em {cat}"

        # 3. Erro com resultado vazio ou ausência de log
        if any(s in full for s in derived_symptoms):
            return True, "Derivado (Falha Oculta de Corpus/Log)", f"Erro de Execução em {cat}"

        # 4. Menção a formatos externos
        if row.get("has_heterogeneous_format"):
            return True, "Derivado (Manipulação de Formato Bruto)", f"Formato Bruto em {cat}"

        return False, "Não Relacionado a Parsing", "Conceitual / Metodologia Pura"

    parsing_results = df.apply(classify_parsing, axis=1)
    df["is_parsing_related"] = [r[0] for r in parsing_results]
    df["parsing_type"] = [r[1] for r in parsing_results]
    df["parsing_cause"] = [r[2] for r in parsing_results]

    df["is_data_processing"] = df["category"] == "Data processing"

    return df, summary


df, summary = load_data()

if df.empty:
    st.stop()

# Cabeçalho
st.markdown('<div style="margin-bottom: 12px;"><span class="tcc-badge">TCC • UFBA 2026</span> <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 8px;">Pesquisa Aplicada • Assistente Sociotécnico para Data Profiling & RAG</span></div>', unsafe_allow_html=True)
st.title("📊 Análise de Fricção em Data Parsing: Evidências Estatísticas do Fórum CorText")
st.markdown("""
**Diagnóstico Empírico da Fricção Sociotécnica em Preparação e Ingestão de Corpora (CorText Manager)**  
*Evidências quantitativas e qualitativas sobre a barreira de entrada enfrentada por pesquisadores na importação e parsing de dados heterogêneos.*
""")

# Indicadores gerais (KPIs)
st.markdown("### 📌 Indicadores Gerais de Fricção")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

total_topics = len(df)
parsing_total_count = int(df["is_parsing_related"].sum())
parsing_total_pct = (parsing_total_count / total_topics) * 100
dp_direct_count = int((df["category"] == "Data processing").sum())
dp_derived_count = parsing_total_count - dp_direct_count

hetero_fmt_pct = (len(df[df["has_heterogeneous_format"]]) / total_topics) * 100
staff_dp_pct = (len(df[(df["category"] == "Data processing") & (df["has_staff_answer"])]) / dp_direct_count) * 100
total_views = int(df["views_count"].sum())

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total de Discussões</div>
        <div class="kpi-value">{total_topics}</div>
        <div class="kpi-sub">34 páginas completas do fórum oficial</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Tópicos com Data Parsing</div>
        <div class="kpi-value">{parsing_total_count} ({parsing_total_pct:.1f}%)</div>
        <div class="kpi-sub">{dp_direct_count} diretos em DP + {dp_derived_count} derivados em outras etapas</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Fontes Heterogêneas</div>
        <div class="kpi-value">{hetero_fmt_pct:.1f}%</div>
        <div class="kpi-sub">Citando CSV, WOS, Scopus, ZIP, RIS</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Dependência do Staff</div>
        <div class="kpi-value">{staff_dp_pct:.1f}%</div>
        <div class="kpi-sub">Em Data processing demandaram suporte</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Visualizações Acumuladas</div>
        <div class="kpi-value">{total_views/1000:.1f}k</div>
        <div class="kpi-sub">Soma dos contadores web oficiais (2014–2026)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="note-box">
    <div style="margin-bottom: 8px;">
        ℹ️ <b>Nota Metodológica sobre o Escopo de Data Parsing (198 tópicos / 66,4% do acervo):</b> Dos 198 tópicos que envolvem preparação de dados, <b>84 são diretos</b> (categoria oficial <code>Data processing</code>) e <b>114 são derivados</b> em etapas posteriores (Network mapping, Text processing, etc.), causados por formatos brutos heterogêneos, indexadores de termos e falhas de encoding. <i>Consulte o detalhamento dos 3 critérios analíticos e heurísticos na <b>Aba 1</b>.</i>
    </div>
    <div>
        👁️ <b>Nota Metodológica sobre as Visualizações (791,7k views):</b> Este valor é a soma exata dos contadores públicos oficiais registrados pelo plugin de fórum do WordPress (<code>dwqa-views-count</code>) em cada uma das 298 páginas desde setembro de 2014. Como os tópicos são públicos e indexados no Google há mais de 11 anos, eles acumulam milhares de acessos orgânicos de pesquisadores internacionais (a <b>mediana é de 2.216 visualizações por tópico</b>).
    </div>
</div>
""", unsafe_allow_html=True)


# Abas de navegação
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 1. Data Parsing Expandido",
    "📁 2. Mapeamento da Fricção por Formato de Entrada",
    "🔍 3. Opacidade & Dependência do Staff",
    "⏳ 4. Persistência Temporal",
    "🔎 5. Central de Consulta dos Tópicos"
])

# Aba 1: Data Parsing Expandido
with tab1:
    st.markdown("#### 1. A Fricção Oculta de Data Parsing Além da Categoria Oficial")
    st.markdown("""
    Um erro comum em análises superficiais de fóruns é olhar apenas a etiqueta oficial do tópico.
    Muitas vezes, um pesquisador abre uma dúvida em **Network Mapping**, mas a causa-raiz não é o algoritmo de rede:
    é um **arquivo CSV com delimitadores corrompidos** ou **colunas de autores mal formatadas no parsing**, gerando o erro de *"rede gerada vazia"*.
    """)

    col_dp1, col_dp2 = st.columns([1, 1])

    with col_dp1:
        # Gráfico direto vs derivado
        type_counts = df["parsing_type"].value_counts().reset_index()
        type_counts.columns = ["Tipo de Envolvimento", "Total de Tópicos"]
        type_counts["Percentual"] = (type_counts["Total de Tópicos"] / len(df)) * 100

        fig_type = px.pie(
            type_counts,
            names="Tipo de Envolvimento",
            values="Total de Tópicos",
            hole=0.45,
            title="Decomposição das Dúvidas: Parsing Direto vs Derivado",
            color_discrete_sequence=["#3b82f6", "#06b6d4", "#94a3b8"]
        )
        fig_type.update_traces(textposition="inside", textinfo="percent+value")
        fig_type.update_layout(showlegend=True, margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_type, use_container_width=True)

    with col_dp2:
        # Quantidade de problemas de Parsing por Categoria
        p_by_cat = df[df["is_parsing_related"]].groupby("category").size().reset_index(name="Tópicos com Parsing")
        tot_by_cat = df.groupby("category").size().reset_index(name="Total da Categoria")
        merged_cat = pd.merge(tot_by_cat, p_by_cat, on="category", how="left").fillna(0)
        merged_cat["% com Parsing"] = (merged_cat["Tópicos com Parsing"] / merged_cat["Total da Categoria"]) * 100
        merged_cat = merged_cat.sort_values(by="Tópicos com Parsing", ascending=True)

        fig_pcat = px.bar(
            merged_cat,
            x="Tópicos com Parsing",
            y="category",
            orientation="h",
            title="Tópicos Envolvendo Data Parsing Presentes em Cada Categoria",
            text="Tópicos com Parsing",
            color="% com Parsing",
            color_continuous_scale="Viridis"
        )
        fig_pcat.update_layout(margin=dict(t=50, b=20, l=20, r=20), yaxis_title="Categoria")
        st.plotly_chart(fig_pcat, use_container_width=True)

    st.markdown("##### 📌 Tabela Detalhada: Decomposição de Data Parsing por Categoria")
    table_cat = merged_cat.sort_values(by="Tópicos com Parsing", ascending=False).copy()
    table_cat.columns = ["Categoria Oficial", "Total de Tópicos", "Tópicos com Data Parsing (Direto ou Derivado)", "% Afetada por Parsing"]
    table_cat["% Afetada por Parsing"] = table_cat["% Afetada por Parsing"].map("{:.1f}%".format)
    st.dataframe(table_cat, use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="note-box" style="margin-top: 18px; margin-bottom: 24px;">
        <div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc; margin-bottom: 8px;">
            📋 Nota Metodológica: Critérios Analíticos e Heurísticos dos 114 Tópicos Derivados de Data Parsing
        </div>
        <p style="margin-bottom: 10px; line-height: 1.6;">
            No fórum oficial do CorText, a categoria é atribuída de maneira discricionária pelo próprio usuário no momento da postagem. Esse formato introduz um <b>viés sistemático de rotulação a jusante</b>: pesquisadores tendem a registrar a dúvida na etapa em que a sua análise final foi interrompida (por exemplo, ao tentar gerar uma rede em <i>Network mapping</i> ou extrair termos em <i>Text processing</i>), e não no ponto de origem da anomalia estrutural.
        </p>
        <p style="margin-bottom: 12px; line-height: 1.6;">
            Enquanto a categoria formal <code>Data processing</code> abrange <b>84 tópicos diretos (28,2% do acervo)</b>, uma auditoria semântica e causal aplicada aos títulos, corpos de dúvidas e respostas identificou que outros <b>114 tópicos</b> em outras 9 categorias do fórum têm como causa-raiz entraves de <i>Data Parsing</i>, normalização e ingestão de corpora. Ao consolidá-los, a barreira real de preparação de dados atinge <b>198 tópicos (66,4% de todo o fórum)</b>.
        </p>
        <div style="font-weight: 600; color: #60a5fa; margin-bottom: 8px;">
            Regras de Elegibilidade e Critérios Heurísticos Aplicados (Total = 114 tópicos derivados):
        </div>
        <ol style="padding-left: 20px; margin-bottom: 14px; line-height: 1.65;">
            <li style="margin-bottom: 10px;">
                <b>Critério 1 — Manipulação de Formatos Brutos Heterogêneos (62 tópicos | 54,4% dos derivados):</b><br/>
                <i>Condição Heurística:</i> Discussões registradas fora de <code>Data processing</code> cuja demanda central envolve o carregamento, conversão, exportação ou delimitação de formatos e bases bibliográficas externas proprietárias (<code>Scopus</code>, <code>Web of Science / WOS</code>, <code>Factiva</code>, <code>PubMed</code>, <code>RIS</code>, <code>ISI</code>, <code>CSV</code>, <code>ZIP</code>, <code>TSV</code>, <code>Excel/XLSX</code>, <code>ProQuest</code>, <code>Istex</code>).<br/>
                <i>Justificativa Epistêmica:</i> A fricção técnica não decorre do algoritmo analítico da ferramenta, mas da rigidez do <i>parser</i> do CorText diante de alterações de leiaute das fontes brutas, ausência de cabeçalhos padrão ou separadores multivalorados (autores/palavras-chave) corrompidos.
            </li>
            <li style="margin-bottom: 10px;">
                <b>Critério 2 — Menção Explícita de Indexação, Encoding e Parsing em Outras Etapas (50 tópicos | 43,9% dos derivados):</b><br/>
                <i>Condição Heurística:</i> Tópicos postados sob rótulos de etapas analíticas posteriores (como <code>Text processing</code>, <code>Network mapping</code> ou <code>Data exploration</code>) que citam expressamente rotinas de ingestão tabular e indexação de corpora (vocábulos: <code>pars</code>, <code>parser</code>, <code>parsing</code>, <code>upload</code>, <code>delimiter</code>, <code>encoding</code>, <code>utf-8</code>, <code>corpus terms indexer</code>, <code>corpus list indexer</code>, <code>importing</code>, <code>subcorpus</code>).<br/>
                <i>Justificativa Epistêmica:</i> O usuário tenta executar scripts de extração de termos ou carregar subcorpus particionados, mas o fluxo falha silenciosamente por caracteres corrompidos (incompatibilidade UTF-8/ISO-8859-1) ou delimitadores não reconhecidos na carga tabular.
            </li>
            <li style="margin-bottom: 10px;">
                <b>Critério 3 — Sintomas Patognomônicos de Corpus Corrompido / Vazio (2 tópicos | 1,8% dos derivados):</b><br/>
                <i>Condição Heurística:</i> Tópicos fora de <code>Data processing</code> apresentando erros críticos a jusante com resultados vazios e ausência de mensagens informativas (ex.: <code>"Network you produced is empty"</code>, <code>"Réseau vide"</code> ou <code>"No logs found"</code>).<br/>
                <i>Justificativa Epistêmica:</i> Quando o grafo gerado possui 0 nós/arestas, a investigação do log técnico revela que o parser inicial descartou integralmente os registros do corpus devido a colunas ausentes ou formatação inválida, sem fornecer feedback preventivo ao pesquisador.
            </li>
        </ol>
        <div style="background: rgba(15, 23, 42, 0.65); padding: 12px 16px; border-radius: 8px; border-left: 3px solid #38bdf8; font-size: 0.84rem; line-height: 1.55;">
            <b>Distribuição Categorial dos 114 Tópicos Derivados:</b><br/>
            • <b>Network mapping:</b> 40 tópicos (50,6% da categoria tem raiz causal em parsing)<br/>
            • <b>Text processing:</b> 34 tópicos (66,7% da categoria tem raiz causal em parsing)<br/>
            • <b>Data exploration:</b> 14 tópicos (70,0% da categoria tem raiz causal em parsing)<br/>
            • <b>Something else:</b> 11 tópicos (33,3% da categoria tem raiz causal em parsing)<br/>
            • <b>Time processing:</b> 7 tópicos (63,6% da categoria tem raiz causal em parsing)<br/>
            • <b>Topic modeling:</b> 4 tópicos (44,4% da categoria tem raiz causal em parsing)<br/>
            • <b>Demais categorias (SASHIMI, Profiling, Spatial, Sem Categoria):</b> 4 tópicos<br/>
            <span style="color: #94a3b8; display: inline-block; margin-top: 6px;">💡 <i>Todos os 114 tópicos derivados e seus respectivos critérios podem ser consultados e filtrados individualmente na <b>Aba 5 (Central de Consulta dos Tópicos)</b>.</i></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 👁️ Volume Absoluto de Visualizações Acumuladas")

    col_v1, col_v2 = st.columns(2)

    with col_v1:
        # Volume total por categoria oficial
        tot_views_cat = df.groupby("category")["views_count"].sum().reset_index().sort_values(by="views_count", ascending=True)
        tot_views_cat.columns = ["Categoria", "Visualizações Totais"]

        fig_tot_views = px.bar(
            tot_views_cat,
            x="Visualizações Totais",
            y="Categoria",
            orientation="h",
            title="Volume Total de Visualizações por Categoria Oficial",
            color="Visualizações Totais",
            color_continuous_scale="Blues",
            text_auto=".2s"
        )
        fig_tot_views.update_layout(margin=dict(t=50, b=20, l=20, r=20), coloraxis_showscale=False)
        st.plotly_chart(fig_tot_views, use_container_width=True)

    with col_v2:
        # Volume total por escopo de parsing (direto vs derivados vs outros)
        scope_views = df.groupby("parsing_type")["views_count"].sum().reset_index().sort_values(by="views_count", ascending=True)
        scope_views.columns = ["Tipo de Envolvimento", "Visualizações Totais"]

        fig_scope_views = px.bar(
            scope_views,
            x="Visualizações Totais",
            y="Tipo de Envolvimento",
            orientation="h",
            title="Volume Total de Visualizações por Tipo de Envolvimento",
            color="Visualizações Totais",
            color_continuous_scale="Teal",
            text_auto=".2s"
        )
        fig_scope_views.update_layout(margin=dict(t=50, b=20, l=20, r=20), coloraxis_showscale=False)
        st.plotly_chart(fig_scope_views, use_container_width=True)

    st.markdown("""
    <div class="note-box">
        <b>💡 Consolidação dos Volumes de Visualizações:</b><br/>
        <ul>
            <li><b>Liderança por Categoria Oficial:</b> <code>Data processing</code> é a <b>líder absoluta de todo o fórum com 237.059 visualizações</b>, superando Network mapping (225k) e Text processing (109k).</li>
            <li><b>Concentração no Escopo Expandido de Parsing:</b> Ao somar os tópicos diretos aos 114 derivados em outras etapas, as discussões sobre Data Parsing concentram <b>526.992 visualizações (66,6% de todo o tráfego acumulado do fórum)</b>, demonstrando que dois terços dos acessos públicos históricos decorrem de barreiras na ingestão e preparação de corpora.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# Aba 2: Mapeamento da Fricção por Formato de Entrada
with tab2:
    st.markdown("#### 2. Mapeamento da Fricção por Formato de Entrada & Fontes Brutas")
    st.markdown("""
    O escopo da pesquisa pontua que a extrema heterogeneidade das bases brutas (Scopus, Factiva, WOS, redes sociais) desafia o tratamento automatizado.
    O gráfico abaixo quantifica quais são os formatos que geram a maior quantidade de dúvidas e chamados de suporte.
    """)

    fmt_list = []
    for fmts in df["detected_formats"]:
        fmt_list.extend(fmts)

    fmt_series = pd.Series(fmt_list).value_counts().reset_index()
    fmt_series.columns = ["Formato / Fonte", "Ocorrências"]
    fmt_series["% do Total de Tópicos"] = (fmt_series["Ocorrências"] / len(df)) * 100

    col_f1, col_f2 = st.columns([3, 2])

    with col_f1:
        fig_fmt = px.bar(
            fmt_series,
            x="Ocorrências",
            y="Formato / Fonte",
            orientation="h",
            title="Ranking de Formatos e Fontes Heterogêneas mais Problemáticos",
            color="Ocorrências",
            color_continuous_scale="Purples",
            text="Ocorrências"
        )
        fig_fmt.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_fmt, use_container_width=True)

    with col_f2:
        st.markdown("##### 📌 Principais Causas de Incompatibilidade")
        st.markdown("""
        1. **CSV / Separadores Tabulares:**
           * Pesquisadores confundem delimitadores de vírgula (`,`), ponto-e-vírgula (`;`) e tabulação (`\\t`).
           * Ausência da coluna de ano de publicação exigida pelo parser.
        2. **Arquivos ZIP:**
           * Falhas ao descompactar estruturas aninhadas originadas de exportações do Factiva ou Scopus.
        3. **Scopus vs Web of Science (WOS):**
           * Exportações em formato RIS com tags customizadas não reconhecidas pelo parser padrão.
           * Codificação de caracteres (`UTF-8` vs `ISO-8859-1` / `Windows-1252`) corrompendo acentuações em corpora multilíngues.
        """)

        st.info("💡 **Oportunidade para o Assistente:** Realizar a checagem prévia de codificação (encoding), contagem de colunas e inferência de delimitador antes de o usuário enviar o job para processamento na nuvem.")


# Aba 3: Opacidade dos Erros e Suporte do Staff
with tab3:
    st.markdown("#### 3. A Opacidade Diagnóstica e o Custo do Atendimento Humano")
    st.markdown("""
    Quando um script de Parsing falha, o backend do CorText frequentemente emite mensagens que não orientam o pesquisador leigo em computação
    (como *"No logs found"* ou erros genéricos de execução). Isso gera uma **sobrecarga na equipe técnica do projeto**, que atua como depurador manual.
    """)

    col_op1, col_op2 = st.columns([1, 1])

    with col_op1:
        staff_comp = pd.DataFrame({
            "Categoria": ["Data Processing (Direto)", "Demais Categorias"],
            "Taxa de Intervenção do Staff (%)": [
                (len(df[(df["category"] == "Data processing") & (df["has_staff_answer"])]) / len(df[df["category"] == "Data processing"])) * 100,
                (len(df[(df["category"] != "Data processing") & (df["has_staff_answer"])]) / len(df[df["category"] != "Data processing"])) * 100
            ]
        })

        fig_staff = px.bar(
            staff_comp,
            x="Categoria",
            y="Taxa de Intervenção do Staff (%)",
            title="Dependência da Equipe Técnica (Staff as Human Parser)",
            color="Categoria",
            color_discrete_sequence=["#ef4444", "#3b82f6"],
            text_auto=".1f"
        )
        fig_staff.update_layout(yaxis=dict(range=[0, 100]), showlegend=False, margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_staff, use_container_width=True)

    with col_op2:
        dp_status = df[df["category"] == "Data processing"]["status"].value_counts().reset_index()
        dp_status.columns = ["Status", "Quantidade"]

        fig_status = px.pie(
            dp_status,
            names="Status",
            values="Quantidade",
            title="Status dos Tópicos em Data Processing",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Sunset
        )
        fig_status.update_traces(textposition="inside", textinfo="percent+label")
        fig_status.update_layout(margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_status, use_container_width=True)

    st.markdown("##### 📝 O Esforço Textual dos Usuários para Descrever Erros")
    col_w1, col_w2 = st.columns([2, 1])

    with col_w1:
        fig_words = px.box(
            df,
            x="category",
            y="question_length_words",
            color="category",
            title="Dispersão da Quantidade de Palavras por Dúvida (Colando Logs e Registros)",
            labels={"category": "Categoria", "question_length_words": "Palavras na Pergunta"}
        )
        fig_words.update_layout(showlegend=False, margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_words, use_container_width=True)

    with col_w2:
        st.markdown("""
        <div class="quote-box">
            <b>Exemplo Real de Registro no Fórum:</b><br/>
            <i>"Prepare Corpus did not finish successfully. See the job log for additional information. However, when I look at the job log, it says 'No logs found'. job id: 446924"</i>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        * Sem o entendimento do erro, usuários colam centenas de linhas de logs crus.
        * A dúvida mais longa de Data Processing possui **1.118 palavras**, reflexo direto da falta de um diagnóstico estruturado prévio (*Data Profiling*).
        """)


# Aba 4: Persistência Temporal (2014 a 2026)
with tab4:
    st.markdown("#### 4. Evolução Temporal da Fricção: Um Problema Permanente")
    st.markdown("""
    O CorText Manager acumula mais de 15 anos de história. Ao analisar o volume de discussões ano a ano (2014 a 2026),
    constata-se que a dificuldade na preparação de dados **não é sazonal nem decorrente de uma versão isolada**,
    mas sim um desafio inerente à expansão de novos repositórios e formatos científicos.
    """)

    yearly = df.groupby(["year_str", "is_parsing_related"]).size().unstack(fill_value=0).reset_index()
    yearly.columns = ["Ano", "Não Relacionado", "Data Parsing (Direto + Derivado)"]
    yearly = yearly[yearly["Ano"] != "Desconhecido"].sort_values(by="Ano")
    yearly["% Parsing"] = (yearly["Data Parsing (Direto + Derivado)"] / (yearly["Data Parsing (Direto + Derivado)"] + yearly["Não Relacionado"])) * 100

    col_t1, col_t2 = st.columns([3, 2])

    with col_t1:
        fig_time = go.Figure()
        fig_time.add_trace(go.Bar(
            x=yearly["Ano"],
            y=yearly["Data Parsing (Direto + Derivado)"],
            name="Envolvendo Data Parsing (Direto + Derivado)",
            marker_color="#3b82f6"
        ))
        fig_time.add_trace(go.Bar(
            x=yearly["Ano"],
            y=yearly["Não Relacionado"],
            name="Outros Temas (Metodologia Pura)",
            marker_color="#64748b"
        ))
        fig_time.update_layout(
            barmode="stack",
            title="Volume Anual de Discussões no Fórum (2014 - 2026)",
            margin=dict(t=50, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_time, use_container_width=True)

    with col_t2:
        fig_pct = px.line(
            yearly,
            x="Ano",
            y="% Parsing",
            title="Proporção Anual de Chamados Envolvendo Parsing (%)",
            markers=True,
            line_shape="spline",
            color_discrete_sequence=["#f59e0b"]
        )
        fig_pct.update_layout(yaxis=dict(range=[0, 100]), margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_pct, use_container_width=True)

    st.markdown("""
    > **Interpretação para a Justificativa do TCC:**  
    > O percentual de chamados envolvendo Data Parsing se mantém predominantemente entre **50% e 75%** ao longo de mais de uma década. Isso comprova que heurísticas automáticas baseadas exclusivamente em regras rígidas de backend são insuficientes para acomodar a dinâmica das bases bibliográficas externas, justificando a inclusão de uma **camada de observabilidade e auxílio metodológico baseada em IA generativa (RAG)**.
    """)


# Aba 5: Central de Consulta aos Tópicos
with tab5:
    st.markdown("#### 🔎 Central de Consulta aos Tópicos do Fórum")
    st.markdown("""
    Consulte e pesquise livremente em todo o acervo empírico de **298 discussões do fórum oficial** do CorText Manager (2014–2026).
    **Todos os filtros de consulta do sistema estão centralizados exclusivamente nesta aba.**
    """)

    # Campo de busca textual principal
    search_query = st.text_input(
        "🔍 Busca por palavras-chave (no título, corpo da dúvida ou autor):",
        value="",
        placeholder="Digite termos como: no logs, scopus, csv, encoding, delimiter, empty network, utf-8, factiva..."
    )

    # Filtros
    with st.container():
        fc1, fc2, fc3, fc4 = st.columns(4)

        with fc1:
            categories_list = ["Todas as Categorias"] + sorted([c for c in df["category"].dropna().unique() if c])
            selected_cat = st.selectbox(
                "🏷️ Categoria / Etapa:",
                categories_list,
                index=0,
                help="Filtra tópicos pela categoria registrada no fórum."
            )

        with fc2:
            parsing_scope = st.selectbox(
                "🎯 Escopo de Data Parsing:",
                [
                    "Todos os Tópicos",
                    "Envolvendo Data Parsing (Direto + Derivado)",
                    "Apenas Direto (Data processing)",
                    "Apenas Derivado (Todos os 114 Tópicos)",
                    "↳ Derivado: Manipulação de Formato Bruto (62)",
                    "↳ Derivado: Indexação/Parsing em Outra Etapa (50)",
                    "↳ Derivado: Falha Oculta de Corpus/Log (2)",
                    "Não Relacionado a Parsing"
                ],
                index=0,
                help="Filtra discussões com base nos critérios diretos ou derivados de Data Parsing."
            )

        with fc3:
            all_formats = sorted(list(set([fmt for sublist in df["detected_formats"] for fmt in sublist])))
            selected_fmt = st.selectbox(
                "📁 Formato Bruto Citado:",
                ["Todos os Formatos"] + all_formats,
                index=0,
                help="Filtra por formato bibliográfico ou tabular mencionado pelo autor."
            )

        with fc4:
            selected_staff = st.selectbox(
                "🛡️ Intervenção do Staff:",
                ["Todos os Níveis", "Apenas com Resposta do Staff", "Sem Resposta do Staff"],
                index=0,
                help="Filtra com base no atendimento da equipe oficial CorText."
            )

    # Aplicação dos filtros
    results = df.copy()

    # 1. Filtro textual
    if search_query.strip():
        q = search_query.strip().lower()
        results = results[
            results["title"].str.lower().str.contains(q, na=False) |
            results["question_body"].str.lower().str.contains(q, na=False) |
            results["author_name"].str.lower().str.contains(q, na=False)
        ]

    # 2. Filtro de categoria
    if selected_cat != "Todas as Categorias":
        results = results[results["category"] == selected_cat]

    # 3. Filtro de parsing
    if parsing_scope == "Envolvendo Data Parsing (Direto + Derivado)":
        results = results[results["is_parsing_related"] == True]
    elif parsing_scope == "Apenas Direto (Data processing)":
        results = results[results["parsing_type"] == "Direto (Data processing)"]
    elif parsing_scope == "Apenas Derivado (Todos os 114 Tópicos)":
        results = results[results["parsing_type"].str.startswith("Derivado")]
    elif "Manipulação de Formato Bruto" in parsing_scope:
        results = results[results["parsing_type"] == "Derivado (Manipulação de Formato Bruto)"]
    elif "Indexação/Parsing em Outra Etapa" in parsing_scope:
        results = results[results["parsing_type"] == "Derivado (Indexação/Parsing em Outra Etapa)"]
    elif "Falha Oculta de Corpus/Log" in parsing_scope:
        results = results[results["parsing_type"] == "Derivado (Falha Oculta de Corpus/Log)"]
    elif parsing_scope == "Não Relacionado a Parsing":
        results = results[results["is_parsing_related"] == False]

    # 4. Filtro de formato
    if selected_fmt != "Todos os Formatos":
        results = results[results["detected_formats"].apply(lambda fmts: selected_fmt in fmts)]

    # 5. Filtro de staff
    if selected_staff == "Apenas com Resposta do Staff":
        results = results[results["has_staff_answer"] == True]
    elif selected_staff == "Sem Resposta do Staff":
        results = results[results["has_staff_answer"] == False]

    # Contagem de resultados e paginação
    col_res_info, col_res_limit = st.columns([3, 2])
    with col_res_info:
        pct_res = (len(results) / len(df)) * 100 if len(df) > 0 else 0
        st.markdown(f"**Tópicos Encontrados:** `{len(results)}` de `{len(df)}` ({pct_res:.1f}%)")
    with col_res_limit:
        selected_limit = st.selectbox(
            "Exibir na tela:",
            options=["10 tópicos", "25 tópicos", "50 tópicos", "Todos os resultados"],
            index=3 if len(results) <= 50 else 0,
            help="Escolha quantos tópicos exibir simultaneamente."
        )

    if selected_limit == "Todos os resultados":
        display_results = results
    else:
        limit_num = int(selected_limit.split()[0])
        display_results = results.head(limit_num)

    if selected_limit != "Todos os resultados" and len(results) > len(display_results):
        st.caption(f"Mostrando os primeiros {len(display_results)} de {len(results)} tópicos encontrados.")

    if results.empty:
        st.info("ℹ️ Nenhum tópico encontrado para a combinação de filtros selecionada. Tente limpar os campos ou buscar por outro termo.")
    else:
        for _, row in display_results.iterrows():
            parsing_tag = "⚙️ Envolve Parsing" if row["is_parsing_related"] else "📘 Outro Tema"
            with st.expander(f"📌 [{row['id']}] {row['title']} (Views: {row['views_count']} | Categoria: {row['category']} | {parsing_tag})"):
                st.markdown(f"**URL Original:** [{row['url']}]({row['url']})")
                st.markdown(f"**Autor:** {row['author_name']} &nbsp;|&nbsp; **Data:** {row['date_published']} &nbsp;|&nbsp; **Status:** {row['status']}")
                st.markdown(f"**Diagnóstico de Parsing:** `{row['parsing_type']}` — *{row['parsing_cause']}*")

                st.markdown("##### ❓ Relato do Usuário (Dúvida):")
                st.markdown(f"```text\n{row['question_body'][:3000]}\n```")

                answers = row.get("answers", [])
                if answers:
                    st.markdown(f"##### 💬 Respostas Registradas ({len(answers)}):")
                    for ans_idx, ans in enumerate(answers, 1):
                        is_staff_badge = "🛡️ Staff do CorText" if "Staff" in ans.get("meta", "") else "Comunidade"
                        is_best_badge = " • ⭐ Melhor Resposta" if ans.get("is_best") else ""
                        st.markdown(f"**Resposta {ans_idx} — {ans.get('author')}** (*{is_staff_badge}*{is_best_badge}):")
                        st.markdown(f"> {ans.get('content')}")
                else:
                    st.warning("Nenhuma resposta registrada para este tópico.")
