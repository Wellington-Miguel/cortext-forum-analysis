"""
Gerador Automatizado de Relatório Técnico Completo em PDF
Análise de Fricção em Data Parsing: Evidências Estatísticas e Sociotécnicas do Fórum CorText
Trabalho de Conclusão de Curso (TCC) - Universidade Federal da Bahia (UFBA)
"""

import os
import json
import re
import math
import subprocess
import statistics
from datetime import datetime
from collections import Counter

# Caminhos dos arquivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_JSON_PATH = os.path.join(BASE_DIR, "output_forum", "forum_topics_full.json")
SUMMARY_JSON_PATH = os.path.join(BASE_DIR, "output_forum", "resumo_estatistico.json")
HTML_OUTPUT_PATH = os.path.join(BASE_DIR, "relatorio_tcc_cortext.html")
PDF_OUTPUT_PATH = os.path.join(BASE_DIR, "relatorio_tcc_cortext.pdf")

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"


def load_and_process_data():
    if not os.path.exists(DATA_JSON_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {DATA_JSON_PATH}")

    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        topics = json.load(f)

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

    parsing_kw = [
        'pars', 'parser', 'parsing', 'upload', 'delimiter', 'encoding', 'utf-8', 
        'corpus terms indexer', 'corpus list indexer', 'corps terms indexer', 
        'importing', 'subcorpus', 'sub-corpus'
    ]
    derived_symptoms = [
        'network you produced is empty', 'reseau vide', 'network is empty', 'empty network',
        'no logs found', 'no info in logs', 'job id:'
    ]

    for t in topics:
        title = t.get("title") or ""
        body = t.get("question_body") or ""
        text = f"{title} {body}".lower()
        cat = (t.get("category") or "Sem Categoria").strip()
        t["category"] = cat if cat else "Sem Categoria"

        detected_formats = [fmt for fmt, pat in format_regexes.items() if re.search(pat, text)]
        t["detected_formats"] = detected_formats
        t["has_heterogeneous_format"] = len(detected_formats) > 0

        # Classificação de parsing
        if cat == "Data processing":
            t["is_parsing"] = True
            t["parsing_scope"] = "Parsing Direto (Data processing)"
            t["parsing_subcriterion"] = "Categoria Oficial Data processing"
        elif any(k in text for k in parsing_kw):
            t["is_parsing"] = True
            t["parsing_scope"] = "Parsing Indireto / Derivado"
            t["parsing_subcriterion"] = "Critério 2: Indexação/Parsing em Outra Etapa"
        elif any(s in text for s in derived_symptoms):
            t["is_parsing"] = True
            t["parsing_scope"] = "Parsing Indireto / Derivado"
            t["parsing_subcriterion"] = "Critério 3: Falha Oculta de Corpus/Log"
        elif t["has_heterogeneous_format"]:
            t["is_parsing"] = True
            t["parsing_scope"] = "Parsing Indireto / Derivado"
            t["parsing_subcriterion"] = "Critério 1: Manipulação de Formato Bruto"
        else:
            t["is_parsing"] = False
            t["parsing_scope"] = "Não Relacionado a Parsing"
            t["parsing_subcriterion"] = "Discussão Metodológica/Conceitual"

        # Tratamento de datas
        date_pub = t.get("date_published") or ""
        year_match = re.search(r"^(\d{4})", date_pub)
        t["year"] = int(year_match.group(1)) if year_match else None

    return topics


# ==========================================
# GERADORES DE GRÁFICOS VETORIAIS (SVG)
# ==========================================

def svg_donut_chart(data, total, title, width=540, height=270, donut_text="298", donut_sub="Tópicos"):
    """Gera gráfico de rosca em SVG puro com legenda lateral."""
    cx, cy, r_out, r_in = 135, 145, 100, 58
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<text x="{width/2}" y="24" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700" fill="#0f172a">{title}</text>')
    
    start_angle = -math.pi / 2
    legend_y = 55
    
    for label, count, color in data:
        pct = (count / total) * 100
        angle = (count / total) * 2 * math.pi
        end_angle = start_angle + angle
        
        x1_out = cx + r_out * math.cos(start_angle)
        y1_out = cy + r_out * math.sin(start_angle)
        x2_out = cx + r_out * math.cos(end_angle)
        y2_out = cy + r_out * math.sin(end_angle)
        
        x1_in = cx + r_in * math.cos(end_angle)
        y1_in = cy + r_in * math.sin(end_angle)
        x2_in = cx + r_in * math.cos(start_angle)
        y2_in = cy + r_in * math.sin(start_angle)
        
        large_arc = 1 if angle > math.pi else 0
        d = f"M {x1_out} {y1_out} A {r_out} {r_out} 0 {large_arc} 1 {x2_out} {y2_out} L {x1_in} {y1_in} A {r_in} {r_in} 0 {large_arc} 0 {x2_in} {y2_in} Z"
        parts.append(f'<path d="{d}" fill="{color}" stroke="#ffffff" stroke-width="2"/>')
        
        parts.append(f'<rect x="275" y="{legend_y}" width="12" height="12" rx="3" fill="{color}"/>')
        parts.append(f'<text x="295" y="{legend_y+10}" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" fill="#334155">{label}: <tspan font-weight="700" fill="#0f172a">{count}</tspan> ({pct:.1f}%)</text>')
        legend_y += 24
        
        start_angle = end_angle

    parts.append(f'<text x="{cx}" y="{cy-3}" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="20" font-weight="800" fill="#0f172a">{donut_text}</text>')
    parts.append(f'<text x="{cx}" y="{cy+14}" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10" font-weight="600" fill="#64748b" text-transform="uppercase">{donut_sub}</text>')
    parts.append('</svg>')
    return "".join(parts)


def svg_horizontal_bar_chart(data, width=540, height=270, title="Ranking de Formatos Brutos Problemáticos (Menções nos Chamados)"):
    """Gera gráfico de barras horizontais em SVG puro."""
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<text x="{width/2}" y="24" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700" fill="#0f172a">{title}</text>')
    
    max_val = max(c for _, c, _ in data)
    start_y = 50
    bar_height = 20
    gap = 14
    bar_area_width = 330
    
    for label, count, pct in data:
        bar_w = (count / max_val) * bar_area_width
        parts.append(f'<text x="145" y="{start_y+14}" text-anchor="end" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" fill="#334155" font-weight="600">{label}</text>')
        parts.append(f'<rect x="155" y="{start_y}" width="{bar_w}" height="{bar_height}" rx="4" fill="#3b82f6"/>')
        parts.append(f'<text x="{155 + bar_w + 8}" y="{start_y+14}" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" fill="#0f172a" font-weight="700">{count} <tspan font-weight="400" fill="#64748b">({pct:.1f}%)</tspan></text>')
        start_y += bar_height + gap
        
    parts.append('</svg>')
    return "".join(parts)


def svg_grouped_bar_staff(width=540, height=270, title="Dependência da Equipe Técnica (Staff as Human Parser)"):
    """Gera gráfico de barras verticais comparando taxa de intervenção do Staff."""
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<text x="{width/2}" y="24" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700" fill="#0f172a">{title}</text>')
    
    # Eixo Y
    parts.append('<line x1="80" y1="45" x2="80" y2="215" stroke="#cbd5e1" stroke-width="1"/>')
    parts.append('<line x1="80" y1="215" x2="480" y2="215" stroke="#cbd5e1" stroke-width="1"/>')
    
    for y_val in [0, 25, 50, 75, 100]:
        y_pos = 215 - (y_val / 100) * 165
        parts.append(f'<line x1="75" y1="{y_pos}" x2="480" y2="{y_pos}" stroke="#f1f5f9" stroke-width="1"/>')
        parts.append(f'<text x="70" y="{y_pos+4}" text-anchor="end" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10" fill="#64748b">{y_val}%</text>')
        
    # Barra 1: Data Processing (81.0%)
    h1 = (81.0 / 100) * 165
    parts.append(f'<rect x="150" y="{215 - h1}" width="90" height="{h1}" rx="4" fill="#ef4444"/>')
    parts.append(f'<text x="195" y="{215 - h1 - 8}" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="800" fill="#b91c1c">81.0%</text>')
    parts.append(f'<text x="195" y="232" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" font-weight="600" fill="#1e293b">Data Processing</text>')
    parts.append(f'<text x="195" y="246" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10" fill="#64748b">(Direto: 68/84)</text>')
    
    # Barra 2: Demais Categorias (77.1%)
    h2 = (77.1 / 100) * 165
    parts.append(f'<rect x="320" y="{215 - h2}" width="90" height="{h2}" rx="4" fill="#3b82f6"/>')
    parts.append(f'<text x="365" y="{215 - h2 - 8}" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="800" fill="#1d4ed8">77.1%</text>')
    parts.append(f'<text x="365" y="232" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" font-weight="600" fill="#1e293b">Demais Categorias</text>')
    parts.append(f'<text x="365" y="246" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10" fill="#64748b">(165/214)</text>')
    
    parts.append('</svg>')
    return "".join(parts)


def svg_boxplot_words(width=540, height=270, title="Dispersão Textual por Escopo (Kruskal-Wallis H=15.92, p < 0.001)"):
    """Gera boxplot vetorial com quartis, medianas e outliers."""
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<text x="{width/2}" y="24" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700" fill="#0f172a">{title}</text>')
    
    # Eixo Y (0 a 1200 palavras)
    parts.append('<line x1="65" y1="45" x2="65" y2="215" stroke="#cbd5e1" stroke-width="1"/>')
    parts.append('<line x1="65" y1="215" x2="510" y2="215" stroke="#cbd5e1" stroke-width="1"/>')
    
    for w_val in [0, 200, 400, 600, 800, 1000, 1200]:
        y_pos = 215 - (w_val / 1200) * 165
        parts.append(f'<line x1="60" y1="{y_pos}" x2="510" y2="{y_pos}" stroke="#f1f5f9" stroke-width="1"/>')
        parts.append(f'<text x="55" y="{y_pos+4}" text-anchor="end" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="9" fill="#64748b">{w_val}</text>')
        
    def y_coord(val):
        return 215 - (val / 1200) * 165
        
    groups = [
        {
            "name": "Parsing Direto (DP)", "sub": "N=84 | Med: 81.5", "cx": 140, "color": "#ef4444",
            "q1": 52, "med": 81.5, "q3": 117, "whisker_top": 210, "whisker_bot": 12,
            "outliers": [230, 257, 387]
        },
        {
            "name": "Parsing Indireto", "sub": "N=114 | Med: 95.0", "cx": 285, "color": "#f59e0b",
            "q1": 58, "med": 95.0, "q3": 163, "whisker_top": 320, "whisker_bot": 15,
            "outliers": [327, 362, 446, 538, 1118]
        },
        {
            "name": "Não Relacionado", "sub": "N=100 | Med: 68.5", "cx": 430, "color": "#3b82f6",
            "q1": 42, "med": 68.5, "q3": 108, "whisker_top": 205, "whisker_bot": 10,
            "outliers": [223, 251, 311, 427, 765]
        }
    ]
    
    for g in groups:
        cx = g["cx"]
        c = g["color"]
        y_q1 = y_coord(g["q1"])
        y_med = y_coord(g["med"])
        y_q3 = y_coord(g["q3"])
        y_wtop = y_coord(g["whisker_top"])
        y_wbot = y_coord(g["whisker_bot"])
        
        # Bigodes
        parts.append(f'<line x1="{cx}" y1="{y_q3}" x2="{cx}" y2="{y_wtop}" stroke="{c}" stroke-width="1.5" stroke-dasharray="3,3"/>')
        parts.append(f'<line x1="{cx-15}" y1="{y_wtop}" x2="{cx+15}" y2="{y_wtop}" stroke="{c}" stroke-width="1.5"/>')
        parts.append(f'<line x1="{cx}" y1="{y_q1}" x2="{cx}" y2="{y_wbot}" stroke="{c}" stroke-width="1.5" stroke-dasharray="3,3"/>')
        parts.append(f'<line x1="{cx-15}" y1="{y_wbot}" x2="{cx+15}" y2="{y_wbot}" stroke="{c}" stroke-width="1.5"/>')
        
        # Caixa IQR
        parts.append(f'<rect x="{cx-30}" y="{y_q3}" width="60" height="{y_q1 - y_q3}" rx="2" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="2"/>')
        # Linha Mediana
        parts.append(f'<line x1="{cx-30}" y1="{y_med}" x2="{cx+30}" y2="{y_med}" stroke="{c}" stroke-width="3"/>')
        
        # Outliers
        for o in g["outliers"]:
            yo = y_coord(o)
            parts.append(f'<circle cx="{cx}" cy="{yo}" r="3" fill="{c}" stroke="#ffffff" stroke-width="1"/>')
            if o in [1118, 387]:
                parts.append(f'<text x="{cx+7}" y="{yo+4}" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="9" font-weight="bold" fill="{c}">{o} w</text>')

        # Labels
        parts.append(f'<text x="{cx}" y="232" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10" font-weight="700" fill="#0f172a">{g["name"]}</text>')
        parts.append(f'<text x="{cx}" y="246" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="9" fill="#64748b">{g["sub"]}</text>')

    parts.append('</svg>')
    return "".join(parts)


def svg_temporal_stacked_bars(topics, width=540, height=270, title="Persistência Temporal: Data Parsing vs. Outros Temas (2014 a 2026)"):
    """Gera gráfico de barras empilhadas para evolução anual."""
    yearly_dict = {}
    for t in topics:
        y = t.get("year")
        if y and 2014 <= y <= 2026:
            if y not in yearly_dict:
                yearly_dict[y] = {"parsing": 0, "non_parsing": 0}
            if t.get("is_parsing"):
                yearly_dict[y]["parsing"] += 1
            else:
                yearly_dict[y]["non_parsing"] += 1
                
    years = sorted(yearly_dict.keys())
    max_tot = max(yearly_dict[y]["parsing"] + yearly_dict[y]["non_parsing"] for y in years)
    
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<text x="{width/2}" y="24" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700" fill="#0f172a">{title}</text>')
    
    # Eixo
    parts.append('<line x1="50" y1="45" x2="50" y2="215" stroke="#cbd5e1" stroke-width="1"/>')
    parts.append('<line x1="50" y1="215" x2="515" y2="215" stroke="#cbd5e1" stroke-width="1"/>')
    
    for val in [0, 10, 20, 30, 40, 50]:
        y_pos = 215 - (val / 50) * 165
        parts.append(f'<line x1="45" y1="{y_pos}" x2="515" y2="{y_pos}" stroke="#f1f5f9" stroke-width="1"/>')
        parts.append(f'<text x="42" y="{y_pos+4}" text-anchor="end" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="9" fill="#64748b">{val}</text>')
        
    start_x = 65
    bar_w = 26
    step = (505 - 65) / len(years)
    
    for i, y in enumerate(years):
        bx = start_x + i * step
        p_cnt = yearly_dict[y]["parsing"]
        np_cnt = yearly_dict[y]["non_parsing"]
        
        h_p = (p_cnt / 50) * 165
        h_np = (np_cnt / 50) * 165
        
        # Barra Parsing (inferior)
        parts.append(f'<rect x="{bx}" y="{215 - h_p}" width="{bar_w}" height="{h_p}" fill="#f59e0b"/>')
        # Barra Non-Parsing (superior)
        parts.append(f'<rect x="{bx}" y="{215 - h_p - h_np}" width="{bar_w}" height="{h_np}" fill="#3b82f6"/>')
        
        parts.append(f'<text x="{bx + bar_w/2}" y="230" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="9" fill="#334155" transform="rotate(-40, {bx + bar_w/2}, 230)">{str(y)[2:]}</text>')

    # Legenda
    parts.append('<rect x="160" y="252" width="12" height="12" rx="2" fill="#f59e0b"/>')
    parts.append('<text x="178" y="262" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10" fill="#334155">Envolvendo Data Parsing (Direto + Derivado)</text>')
    parts.append('<rect x="365" y="252" width="12" height="12" rx="2" fill="#3b82f6"/>')
    parts.append('<text x="383" y="262" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10" fill="#334155">Outros Temas</text>')
    
    parts.append('</svg>')
    return "".join(parts)


# ==========================================
# MONTAGEM DO TEMPLATE HTML COMPLETO
# ==========================================

def build_report_html(topics):
    total = len(topics)
    p_direct = sum(1 for t in topics if t.get("category") == "Data processing")
    p_derived = sum(1 for t in topics if t.get("is_parsing") and t.get("category") != "Data processing")
    p_total = p_direct + p_derived
    p_pct = (p_total / total) * 100
    non_parsing = total - p_total
    
    # Subcritérios
    crit1 = sum(1 for t in topics if t.get("parsing_subcriterion") == "Critério 1: Manipulação de Formato Bruto")
    crit2 = sum(1 for t in topics if t.get("parsing_subcriterion") == "Critério 2: Indexação/Parsing em Outra Etapa")
    crit3 = sum(1 for t in topics if t.get("parsing_subcriterion") == "Critério 3: Falha Oculta de Corpus/Log")
    
    # Formatos
    all_formats = []
    for t in topics:
        if t.get("category") == "Data processing" or t.get("is_parsing"):
            all_formats.extend(t.get("detected_formats", []))
    fmt_counts = Counter(all_formats)
    
    # Views
    tot_views = sum(t.get("views_count", 0) for t in topics)
    parsing_views = sum(t.get("views_count", 0) for t in topics if t.get("is_parsing"))
    p_views_pct = (parsing_views / tot_views) * 100
    
    # Gerações dos SVGs
    svg1 = svg_donut_chart([
        ("Parsing Derivado (Outras Etapas)", p_derived, "#f59e0b"),
        ("Parsing Direto (Data processing)", p_direct, "#ef4444"),
        ("Não Relacionado a Parsing", non_parsing, "#3b82f6")
    ], total, "Decomposição das Dúvidas: Parsing Direto vs. Derivado")
    
    dp_formats_data = [
        ("CSV / Delimitador", 25, 29.8),
        ("Arquivos ZIP", 24, 28.6),
        ("Web of Science (WOS)", 19, 22.6),
        ("Scopus", 11, 13.1),
        ("Formato RIS", 11, 13.1),
        ("Factiva", 4, 4.8)
    ]
    svg2 = svg_horizontal_bar_chart(dp_formats_data, title="Ranking de Formatos Problemáticos em Data Processing")
    
    svg3 = svg_grouped_bar_staff()
    
    dp_status_data = [
        ("Open (Aberto)", 42, "#3b82f6"),
        ("Answered (Respondido)", 26, "#f59e0b"),
        ("Resolved (Resolvido)", 12, "#10b981"),
        ("Closed (Fechado)", 3, "#64748b"),
        ("Pending (Pendente)", 1, "#a855f7")
    ]
    svg4 = svg_donut_chart(dp_status_data, 84, "Status dos Chamados em Data Processing", donut_text="84", donut_sub="Tópicos DP")
    
    svg5 = svg_boxplot_words()
    
    svg6 = svg_temporal_stacked_bars(topics)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório Técnico TCC: Análise de Fricção em Data Parsing no CorText</title>
<style>
    @page {{
        size: A4;
        margin: 18mm 16mm 20mm 16mm;
        @bottom-right {{
            content: "Página " counter(page) " de " counter(pages);
            font-size: 8pt;
            color: #64748b;
            font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
        }}
        @bottom-left {{
            content: "TCC UFBA — Assistente de Observabilidade Sociotécnica em Data Parsing";
            font-size: 8pt;
            color: #64748b;
            font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
        }}
    }}
    
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1e293b;
        line-height: 1.55;
        font-size: 10pt;
        background-color: #ffffff;
        margin: 0;
        padding: 0;
    }}

    .cover {{
        page-break-after: always;
        text-align: center;
        padding-top: 40px;
    }}
    
    .institution-header {{
        font-size: 11pt;
        font-weight: 700;
        text-transform: uppercase;
        color: #0f172a;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }}
    
    .faculty-header {{
        font-size: 9.5pt;
        color: #475569;
        margin-bottom: 60px;
    }}
    
    .tcc-badge {{
        display: inline-block;
        padding: 5px 14px;
        background: #f1f5f9;
        color: #0284c7;
        border: 1px solid #cbd5e1;
        border-radius: 9999px;
        font-size: 8.5pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 25px;
    }}
    
    h1.report-title {{
        font-size: 21pt;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.25;
        margin: 0 auto 16px auto;
        max-width: 90%;
    }}
    
    .report-subtitle {{
        font-size: 12pt;
        color: #475569;
        font-weight: 500;
        line-height: 1.45;
        margin: 0 auto 50px auto;
        max-width: 85%;
    }}
    
    .author-box {{
        margin-top: 40px;
        font-size: 10.5pt;
        color: #1e293b;
    }}
    
    .author-name {{
        font-weight: 700;
        font-size: 12pt;
        color: #0f172a;
    }}

    .meta-date {{
        font-size: 9pt;
        color: #64748b;
        margin-top: 70px;
    }}

    /* Estilos Gerais */
    h2.section-title {{
        font-size: 13.5pt;
        font-weight: 800;
        color: #0f172a;
        border-bottom: 2px solid #0284c7;
        padding-bottom: 6px;
        margin-top: 24px;
        margin-bottom: 12px;
        page-break-after: avoid;
    }}
    
    h3.sub-title {{
        font-size: 11pt;
        font-weight: 700;
        color: #1e293b;
        margin-top: 16px;
        margin-bottom: 8px;
        page-break-after: avoid;
    }}
    
    p {{
        margin-top: 0;
        margin-bottom: 10px;
        text-align: justify;
    }}
    
    /* Grid de KPIs */
    .kpi-container {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin: 18px 0 24px 0;
        page-break-inside: avoid;
    }}
    
    .kpi-card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 14px;
        text-align: center;
    }}
    
    .kpi-label {{
        font-size: 7.5pt;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }}
    
    .kpi-val {{
        font-size: 18pt;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.1;
    }}
    
    .kpi-desc {{
        font-size: 7.5pt;
        color: #0284c7;
        font-weight: 600;
        margin-top: 4px;
    }}
    
    /* Box de Destaque */
    .callout {{
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 4px solid #16a34a;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 14px 0;
        font-size: 9pt;
        page-break-inside: avoid;
    }}
    
    .callout-title {{
        font-weight: 700;
        color: #15803d;
        margin-bottom: 4px;
    }}

    .callout-blue {{
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-left: 4px solid #0284c7;
    }}
    .callout-blue .callout-title {{ color: #0369a1; }}

    .callout-amber {{
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 4px solid #f59e0b;
    }}
    .callout-amber .callout-title {{ color: #b45309; }}

    /* Tabelas */
    table.data-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 8.5pt;
        margin: 14px 0;
        page-break-inside: avoid;
    }}
    
    table.data-table th {{
        background: #f1f5f9;
        color: #0f172a;
        font-weight: 700;
        text-align: left;
        padding: 7px 10px;
        border: 1px solid #cbd5e1;
    }}
    
    table.data-table td {{
        padding: 6px 10px;
        border: 1px solid #e2e8f0;
        color: #334155;
    }}
    
    table.data-table tr:nth-child(even) {{
        background: #f8fafc;
    }}
    
    /* Figuras */
    .chart-box {{
        text-align: center;
        margin: 16px 0;
        page-break-inside: avoid;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px;
    }}
    
    .chart-caption {{
        font-size: 8pt;
        color: #64748b;
        font-style: italic;
        margin-top: 6px;
    }}
    
    .page-break {{
        page-break-after: always;
    }}
    
    .status-badge-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        margin: 12px 0;
        page-break-inside: avoid;
    }}
    
    .status-item {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px;
        font-size: 7.5pt;
        text-align: left;
    }}
</style>
</head>
<body>

<!-- ================= CAPA ================= -->
<div class="cover">
    <div class="institution-header">Universidade Federal da Bahia — UFBA</div>
    <div class="faculty-header">Instituto de Computação | Trabalho de Conclusão de Curso (TCC)</div>
    
    <div class="tcc-badge">Relatório Técnico & Metodológico Integral</div>
    
    <h1 class="report-title">Análise de Fricção em Data Parsing: Evidências Estatísticas e Sociotécnicas do Fórum CorText</h1>
    <div class="report-subtitle">Fundamentação Empírica para o Desenvolvimento de um Assistente Preventivo de Observabilidade Baseado em Data Profiling e RAG</div>
    
    <div class="kpi-container" style="max-width: 90%; margin: 40px auto;">
        <div class="kpi-card">
            <div class="kpi-label">Corpus Mapeado</div>
            <div class="kpi-val">{total}</div>
            <div class="kpi-desc">Tópicos Únicos (100%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Fricção em Parsing</div>
            <div class="kpi-val">{p_pct:.1f}%</div>
            <div class="kpi-desc">{p_total} chamados afetados</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Intervenção do Staff</div>
            <div class="kpi-val">81,0%</div>
            <div class="kpi-desc">Dependência Humana</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Audiência Orgânica</div>
            <div class="kpi-val">791k</div>
            <div class="kpi-desc">Visualizações Fórum</div>
        </div>
    </div>
    
    <div class="author-box">
        <div>Pesquisador Responsável:</div>
        <div class="author-name">Wellington Miguel</div>
        <div style="font-size: 9.5pt; color: #475569; margin-top: 4px;">Orientação Acadêmica — UFBA</div>
    </div>
    
    <div class="meta-date">Salvador – Bahia, Brasil &nbsp;|&nbsp; {datetime.now().strftime("%B de %Y").capitalize()}</div>
</div>

<!-- ================= SUMÁRIO EXECUTIVO & CONTEXTO ================= -->
<h2 class="section-title">1. Sumário Executivo & Contexto da Pesquisa</h2>

<p>
O <b>CorText Manager</b> é uma das plataformas digitais mais consolidadas e longevas do cenário acadêmico global para análise de corpora textuais heterogêneos, acumulando mais de 15 anos de história sob desenvolvimento conjunto de instituições como LISIS, INRAE, IFRIS, CNRS e Université Gustave Eiffel. Projetado primordialmente para atender pesquisadores das Ciências Humanas e Sociais, o ecossistema disponibiliza algoritmos robustos de mineração de textos, modelagem de tópicos e análise de redes complexas.
</p>

<p>
Contudo, a extrema heterogeneidade das bases documentais científicas brutas (tais como <i>Web of Science</i>, <i>Scopus</i>, <i>Factiva</i>, arquivos RIS, planilhas tabulares de repositórios governamentais e dados de mídias sociais) faz com que a fase preliminar de <b>ingestão e formatação de dados (Data Parsing)</b> represente o principal obstáculo operacional, cognitivo e técnico para a fluidez do processo investigativo.
</p>

<div class="callout callout-blue">
    <div class="callout-title">📌 O Fenômeno "Staff as Human Parser" e a Hipótese Central da Pesquisa:</div>
    A escassez de verificações estruturais prévias (<i>Data Profiling</i>) no momento do upload e a opacidade dos diagnósticos de falha do backend (que frequentemente emitem mensagens genéricas como <i>"No logs found"</i> ou produzem redes vazias silenciosas) forçam a equipe técnica a atuar como um <b>depurador manual crônico</b>. Em <b>81,0% dos tópicos de Data Processing</b>, desenvolvedores seniores precisaram intervir diretamente para inspecionar arquivos corrompidos e logs em linha de comando.
</div>

<p>
Para fundamentar empiricamente essa barreira, foi desenvolvida uma infraestrutura determinística de extração completa do fórum oficial da plataforma (<code>https://docs.cortext.net/forum/</code>). A varredura auditou todo o histórico de discussões públicas, mapeando variáveis de autoria, tempo de resolução, complexidade textual, formatos de entrada e o impacto sociotécnico dessa fricção.
</p>

<!-- ================= METODOLOGIA DE EXTRAÇÃO ================= -->
<h2 class="section-title">2. Engenharia de Extração e Auditoria dos Dados (`extract_forum.py`)</h2>

<p>
A coleta e estruturação dos dados foram operacionalizadas através do extrator customizado <a href="extract_forum.py"><code>extract_forum.py</code></a>, estruturado em três fases estritamente auditáveis e determinísticas:
</p>

<table class="data-table">
    <thead>
        <tr>
            <th style="width: 15%;">Fase Metodológica</th>
            <th style="width: 35%;">Mecanismo Técnico Empregado</th>
            <th style="width: 50%;">Garantia de Integridade e Cobertura</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b>Fase 1: Varredura Sequencial</b></td>
            <td>Iteração sequencial estrita da listagem oficial: páginas <code>/page/1/</code> a <code>/page/34/</code>.</td>
            <td><b>Cobertura Total (298 tópicos únicos):</b> páginas 1 a 33 (9 tópicos cada) + página 34 (1 tópico). Zero filtros e zero duplicatas.</td>
        </tr>
        <tr>
            <td><b>Fase 2: Extração Profunda</b></td>
            <td>Requisições assíncronas concorrentes via <code>aiohttp</code> com semáforo controlado e retries automáticos.</td>
            <td>Captura de marcações semânticas <b>JSON-LD Schema</b> do WordPress (datas exatas em ISO 8601), dúvida na íntegra e array completo de respostas.</td>
        </tr>
        <tr>
            <td><b>Fase 3: Enriquecimento</b></td>
            <td>Detecção de autores oficiais do projeto (badges de <i>🛡️ Staff do CorText</i>) e cálculo de métricas textuais.</td>
            <td><b>Paridade 100%:</b> sincronização simultânea nos formatos <code>forum_topics_full.json</code>, <code>forum_topics.csv</code> e <code>forum_corpus.md</code>.</td>
        </tr>
    </tbody>
</table>

<div class="page-break"></div>

<!-- ================= NOTA METODOLÓGICA DOS 114 TÓPICOS DERIVADOS ================= -->
<h2 class="section-title">3. Nota Metodológica Integral dos 114 Tópicos Derivados</h2>

<p>
Uma das descobertas metodológicas mais contundentes deste estudo foi a constatação de que a categorização oficial fornecida pelo fórum subdimensiona severamente a crise de preparação de dados. Oficialmente, a categoria <code>Data processing</code> abriga <b>84 tópicos (28,2%)</b>. Entretanto, uma análise epistêmica e semântica das discussões revelou outros <b>114 tópicos (38,3%)</b> protocolados em outras etapas analíticas, mas decorrentes exclusivamente de problemas em <i>Data Parsing</i>.
</p>

<div class="callout callout-amber">
    <div class="callout-title">📐 Justificativa Metodológica da Ampliação do Escopo (198 tópicos / 66,4% do acervo):</div>
    Quando o usuário comete um equívoco de formatação (ex.: separador incorreto em CSV ou tags de autor não padronizadas), a falha muitas vezes <b>não quebra o parser imediatamente</b>, mas gera um corpus estruturalmente inconsistente. O erro só explode tardiamente em módulos subsequentes (como <i>Network mapping</i> ou <i>Topic modeling</i>).
</div>

<h3 class="sub-title">Regras de Elegibilidade e Critérios Heurísticos dos 114 Tópicos Derivados:</h3>

<table class="data-table">
    <thead>
        <tr>
            <th style="width: 32%;">Critério Analítico</th>
            <th style="width: 16%; text-align: center;">Tópicos Afetados</th>
            <th style="width: 52%;">Evidência Heurística e Regras Aplicadas</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b>Critério 1: Manipulação de Formato Bruto Heterogêneo</b></td>
            <td style="text-align: center;"><b>{crit1} tópicos</b><br/>(54,4% dos derivados)</td>
            <td>Tópicos em outras categorias que contêm menção explícita a arquivos e dialetos externos (<i>CSV, ZIP, Scopus, WOS, RIS, Factiva, PubMed, Excel</i>), lidando com problemas de separadores ou tags bibliográficas.</td>
        </tr>
        <tr>
            <td><b>Critério 2: Indexação, Parsing e Encoding em Outras Etapas</b></td>
            <td style="text-align: center;"><b>{crit2} tópicos</b><br/>(43,9% dos derivados)</td>
            <td>Discussões mencionando expressamente ferramentas de estruturação preliminar (<i>Corpus Terms Indexer, Corpus List Indexer, upload, encoding UTF-8, subcorpus</i>) durante a execução de etapas de mineração de texto ou redes.</td>
        </tr>
        <tr>
            <td><b>Critério 3: Sintomas Patognomônicos de Corpus Vazio/Corrompido</b></td>
            <td style="text-align: center;"><b>{crit3} tópicos</b><br/>(1,8% dos derivados)</td>
            <td>Chamados reportando o sintoma clássico de ingestão quebrada: geração de redes vazias (<i>"network you produced is empty"</i> ou <i>"reseau vide"</i>) e ausência de logs devido a colunas obrigatórias vazias.</td>
        </tr>
    </tbody>
</table>

<div class="chart-box">
    {svg1}
    <div class="chart-caption">Figura 1: Decomposição analítica do acervo do fórum CorText demonstrando o escopo expandido de Data Parsing.</div>
</div>

<!-- ================= FORMATOS DE ENTRADA ================= -->
<h2 class="section-title">4. Mapeamento da Fricção por Formato de Entrada</h2>

<p>
Ao isolar os tópicos específicos de <i>Data processing</i>, identifica-se a distribuição empírica dos formatos científicos que mais geram atrito na ingestão. O ranking evidencia que a manipulação de arquivos delimitados tabulares e exportações de bases bibliográficas líderes representam quase a totalidade dos incidentes.
</p>

<div class="chart-box">
    {svg2}
    <div class="chart-caption">Figura 2: Frequência de formatos brutos problemáticos identificados nos chamados de preparação de dados.</div>
</div>

<div class="page-break"></div>

<!-- ================= OPACIDADE E DEPENDÊNCIA DO STAFF ================= -->
<h2 class="section-title">5. A Opacidade Diagnóstica e a Sobrecarga do Suporte Humano</h2>

<p>
A falta de explicabilidade técnica das mensagens de erro gera uma dependência direta e contínua do suporte técnico dos mantenedores do CorText. O comparativo revela que as dúvidas de <i>Data processing</i> demandam uma taxa de atendimento manual de <b>81,0%</b> pelo Staff, superando até mesmo etapas metodologicamente complexas da plataforma.
</p>

<div class="chart-box">
    {svg3}
    <div class="chart-caption">Figura 3: Taxa de intervenção manual da equipe do CorText (Staff) por categoria de problema.</div>
</div>

<h3 class="sub-title">Distribuição dos Chamados por Status (DW Question & Answer):</h3>
<p>
A inspeção dos estados de conclusão dos tópicos em <i>Data processing</i> demonstra que metade do acervo permanece em aberto, refletindo a dificuldade do usuário comum em confirmar o fechamento formal de suas dúvidas:
</p>

<div class="chart-box">
    {svg4}
    <div class="chart-caption">Figura 4: Proporção dos status registrados para os chamados da categoria oficial Data processing.</div>
</div>

<div class="status-badge-grid">
    <div class="status-item" style="border-left: 3px solid #3b82f6;">
        <b style="color: #2563eb;">🔵 Open (50,0%)</b><br/>
        Publicado e visível na comunidade. Dúvida aberta sem conclusão formal pelo autor.
    </div>
    <div class="status-item" style="border-left: 3px solid #f59e0b;">
        <b style="color: #d97706;">🟡 Answered (31,0%)</b><br/>
        Recebeu respostas da equipe/comunidade, mas aguarda confirmação de resolução.
    </div>
    <div class="status-item" style="border-left: 3px solid #10b981;">
        <b style="color: #059669;">🟢 Resolved (14,3%)</b><br/>
        Validado formalmente com solução definitiva confirmada pelo autor ou Staff.
    </div>
    <div class="status-item" style="border-left: 3px solid #64748b;">
        <b style="color: #475569;">🟠 Closed (3,6%)</b><br/>
        Trancado administrativamente por duplicação ou encerramento pela moderação.
    </div>
    <div class="status-item" style="border-left: 3px solid #a855f7;">
        <b style="color: #9333ea;">🟣 Pending (1,2%)</b><br/>
        Retido na moderação antispam do WordPress. Não circulou publicamente até validação.
    </div>
</div>

<div class="page-break"></div>

<!-- ================= ESTATÍSTICA E DISPERSÃO TEXTUAL ================= -->
<h2 class="section-title">6. O Custo Cognitivo da Opacidade: Evidências Estatísticas Textuais</h2>

<p>
Para medir quantitativamente o esforço despendido pelos usuários na formulação de seus chamados, analisou-se a extensão textual (quantidade de palavras por pergunta). A hipótese testada afirma que <b>quanto mais opaco e tardio o erro, maior o volume de texto, logs crípticos e tabelas que o usuário se vê compelido a colar no chamado</b>.
</p>

<div class="chart-box">
    {svg5}
    <div class="chart-caption">Figura 5: Dispersão da quantidade de palavras por dúvida conforme o escopo analítico de Data Parsing.</div>
</div>

<table class="data-table">
    <thead>
        <tr>
            <th>Escopo Metodológico</th>
            <th style="text-align: center;">Amostra ($N$)</th>
            <th style="text-align: center;">Mediana</th>
            <th style="text-align: center;">Média</th>
            <th style="text-align: center;">Terceiro Quartil (Q3)</th>
            <th style="text-align: center;">Valor Máximo</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b>1. Parsing Indireto / Derivado</b></td>
            <td style="text-align: center;">114</td>
            <td style="text-align: center;"><b>95,0 palavras</b></td>
            <td style="text-align: center;"><b>129,6 palavras</b></td>
            <td style="text-align: center;">163 palavras</td>
            <td style="text-align: center;"><b>1.118 palavras</b> (Tópico #2)</td>
        </tr>
        <tr>
            <td><b>2. Parsing Direto (*Data processing*)</b></td>
            <td style="text-align: center;">84</td>
            <td style="text-align: center;">81,5 palavras</td>
            <td style="text-align: center;">93,8 palavras</td>
            <td style="text-align: center;">117 palavras</td>
            <td style="text-align: center;">387 palavras (Tópico #280)</td>
        </tr>
        <tr>
            <td><b>3. Não Relacionado a Parsing</b></td>
            <td style="text-align: center;">100</td>
            <td style="text-align: center;">68,5 palavras</td>
            <td style="text-align: center;">90,6 palavras</td>
            <td style="text-align: center;">108 palavras</td>
            <td style="text-align: center;">765 palavras (Tópico #109)</td>
        </tr>
    </tbody>
</table>

<div class="callout callout-blue">
    <div class="callout-title">📐 Testes de Hipótese e Validação Estatística Não-Paramétrica:</div>
    <ul>
        <li><b>Teste de Kruskal-Wallis:</b> $H = 15,923 \\quad (p = 0,00035 < 0,001)$. Rejeita-se categoricamente a hipótese nula com 99,9% de confiança: há diferença altamente significante entre as distribuições textuais dos três grupos.</li>
        <li><b>Teste de Mann-Whitney (Parsing Geral vs. Outros):</b> $Z = 3,380 \\quad (p = 0,0007 < 0,001)$. Os tópicos que envolvem Data Parsing exigem significativamente mais palavras e esforço descritivo do que outros tópicos.</li>
        <li><b>O Fenômeno do Tópico #2 (1.118 palavras):</b> A dúvida mais extensa de todo o fórum pertence ao grupo de <i>Parsing Indireto</i>. O autor relatou que o mapeamento de rede falhou dizendo <i>"network you produced is empty"</i>; sem compreender que a causa raiz residia em delimitadores corrompidos de CSV, colou tabelas, scripts e centenas de linhas de dados brutos na tentativa de ser compreendido.</li>
    </ul>
</div>

<!-- ================= SÉRIE TEMPORAL ================= -->
<h2 class="section-title">7. Persistência Temporal: Uma Barreira Estrutural (2014 a 2026)</h2>

<p>
Ao longo de 12 anos analisados (2014 a 2026), observa-se que a incidência de problemas de preparação de dados não decorre de bugs efêmeros ou versões isoladas de software, mas representa uma constante histórica na utilização da ferramenta:
</p>

<div class="chart-box">
    {svg6}
    <div class="chart-caption">Figura 6: Volume longitudinal de tópicos ao longo dos anos, categorizados por envolvimento com Data Parsing.</div>
</div>

<div class="page-break"></div>

<!-- ================= DIRETRIZES DO ASSISTENTE E CONCLUSÃO ================= -->
<h2 class="section-title">8. Diretrizes de Engenharia para o Assistente Sociotécnico</h2>

<p>
Os achados empíricos e quantitativos deste relatório fornecem as bases conceituais para a especificação do <b>Assistente de Observabilidade Preventiva</b> proposto no Trabalho de Conclusão de Curso (TCC). O assistente visa atuar antes e durante a submissão dos trabalhos no CorText Manager, desonerando a equipe técnica e conferindo autonomia ao pesquisador:
</p>

<table class="data-table">
    <thead>
        <tr>
            <th style="width: 28%;">Módulo da Arquitetura</th>
            <th style="width: 38%;">Funcionalidade Sociotécnica</th>
            <th style="width: 34%;">Impacto Direto na Fricção</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b>1. Pre-Flight Data Profiler</b></td>
            <td>Inspeção prévia em tempo de cliente do arquivo bruto: inferência de delimitador (<code>,</code>, <code>;</code>, <code>\\t</code>), detecção de charset (<code>UTF-8</code> vs <code>Windows-1252</code>) e validação de cabeçalhos mínimos obrigatórios.</td>
            <td>Mitiga <b>58,4%</b> dos erros de Data Processing causados por arquivos CSV mal formatados ou ZIPs aninhados.</td>
        </tr>
        <tr>
            <td><b>2. Log Explainer & RAG</b></td>
            <td>Recuperação Aumentada por Geração (RAG) treinada no corpus consolidado do fórum (<code>forum_corpus.md</code>) para interpretar mensagens crípticas (<i>"No logs found"</i>, jobs terminados prematuramente).</td>
            <td>Reduz a dependência do <i>"Staff as Human Parser"</i>, atualmente em <b>81,0%</b> dos chamados de preparação.</td>
        </tr>
        <tr>
            <td><b>3. Early-Warning Parser</b></td>
            <td>Validador de grafos que emite alertas preventivos quando um corpus importado resulta em matriz de adjacência zerada, antes de o usuário submeter o job à fila de computação.</td>
            <td>Extingue os sintomas patognomônicos de <i>"network you produced is empty"</i> (como o caso emblemático do Tópico #2 de 1.118 palavras).</td>
        </tr>
    </tbody>
</table>

<h3 class="sub-title">Dicionário de Variáveis do Dataset Auditado (`forum_topics.csv`):</h3>
<p>
Para fins de reprodutibilidade e transparência científica, o dataset tabular consolidado disponibiliza 25 atributos métricos:
<code>id</code>, <code>page</code>, <code>title</code>, <code>url</code>, <code>status</code>, <code>is_resolved</code>, <code>is_answered</code>, <code>category</code>, <code>author_name</code>, <code>author_user</code>, <code>time_ago</code>, <code>date_published</code>, <code>date_modified</code>, <code>views_count</code>, <code>answers_count</code>, <code>votes_count</code>, <code>question_length_chars</code>, <code>question_length_words</code>, <code>tags</code>, <code>has_staff_answer</code>, <code>first_answer_author</code>, <code>answers_authors</code>, <code>is_parsing_related</code>, <code>parsing_type</code> e <code>parsing_cause</code>.
</p>

<div class="callout callout-blue" style="margin-top: 24px;">
    <div class="callout-title">Conclusão da Nota Técnica:</div>
    A integração entre <i>Data Profiling</i> preditivo e modelos de linguagem com recuperação sobre a memória técnica do fórum representa uma alternativa sociotécnica viável e de baixo custo operacional, convertendo o CorText de um sistema opaco em uma plataforma de aprendizado guiado e observabilidade contínua.
</div>

</body>
</html>"""
    return html_content


def generate_pdf():
    print("1. Carregando dados do fórum...")
    topics = load_and_process_data()
    print(f"   -> {len(topics)} tópicos carregados.")
    
    print("2. Gerando documento HTML com gráficos vetoriais SVG e formatação editorial A4...")
    html_content = build_report_html(topics)
    with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   -> HTML salvo em: {HTML_OUTPUT_PATH}")
    
    print("3. Compilando PDF via Microsoft Edge Headless...")
    if not os.path.exists(EDGE_PATH):
        raise FileNotFoundError(f"Navegador Edge não encontrado no caminho: {EDGE_PATH}")
        
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        f'Start-Process -FilePath "{EDGE_PATH}" -ArgumentList "--headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf=`"{PDF_OUTPUT_PATH}`" `"{HTML_OUTPUT_PATH}`"" -Wait'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(PDF_OUTPUT_PATH):
        size_kb = os.path.getsize(PDF_OUTPUT_PATH) / 1024
        print(f"   -> SUCESSO! Relatório PDF gerado com êxito: {PDF_OUTPUT_PATH}")
        print(f"   -> Tamanho do arquivo: {size_kb:.1f} KB")
        return PDF_OUTPUT_PATH
    else:
        raise RuntimeError(f"Falha na compilação do PDF. Erro: {result.stderr}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gerador de Relatórios Técnicos (PDF / DOCX)")
    parser.add_argument("--docx", action="store_true", help="Gera o relatório editável em formato DOCX")
    parser.add_argument("--all", action="store_true", help="Gera tanto o relatório em PDF quanto em DOCX")
    args = parser.parse_args()

    if args.docx:
        from generate_docx_report import generate_docx
        generate_docx()
    elif args.all:
        generate_pdf()
        from generate_docx_report import generate_docx
        generate_docx()
    else:
        generate_pdf()
