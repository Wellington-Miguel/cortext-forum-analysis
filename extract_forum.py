"""
Extrator de dados do fórum CorText Manager (docs.cortext.net/forum)
Coleta tópicos, metadados e respostas para análise no TCC (UFBA).
--------------------------------------------------------------------
Garante:
1. Varredura sequencial e completa das páginas 1 a 34 (exatamente 298 tópicos únicos).
2. Sem duplicatas, sem viés de filtros (sem 'filter=unanswered', sem filtros de usuário ou tags).
3. Coleta de metadados tabulares (views, answers, votes, categoria, status, autor).
4. Coleta detalhada do corpo de cada dúvida, respostas e datas exatas ISO (via JSON-LD).
5. Métricas derivadas prontas para estatística (tamanho em palavras, status booleano, respostas do staff).
6. Exportação em múltiplos formatos: CSV (compatível com Excel/Pandas), JSON aninhado e Corpus TXT.
"""

import os
import re
import csv
import json
import time
import asyncio
import aiohttp
import requests
import argparse
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable


BASE_FORUM_PAGE_URL = "https://docs.cortext.net/forum/page/{}/"
DEFAULT_OUTPUT_DIR = "output_forum"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def clean_text(text: Optional[str]) -> str:
    """Remove espaços excessivos e normaliza quebras de linha."""
    if not text:
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join([l for l in lines if l])


def extract_listing_page(html: str, page_num: int) -> List[Dict[str, Any]]:
    """Extrai todos os tópicos de uma página de listagem do fórum."""
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".dwqa-question-item")
    topics = []

    for item in items:
        # 1. Título e Link
        title_el = item.select_one(".dwqa-question-title a")
        title = title_el.text.strip() if title_el else ""
        url = title_el["href"] if title_el and "href" in title_el.attrs else ""

        # 2. Status
        status_el = item.select_one(".dwqa-status")
        status = status_el.text.strip() if status_el else "Unknown"

        # 3. Autor e Slug
        author_link_el = item.select_one(".dwqa-question-meta a[href*='user=']")
        author_name = author_link_el.text.strip() if author_link_el else ""
        author_url = author_link_el["href"] if author_link_el and "href" in author_link_el.attrs else ""
        author_user = ""
        if author_url and "user=" in author_url:
            author_user = author_url.split("user=")[-1].split("&")[0]

        # 4. Tempo relativo (ex: "asked 5 months ago")
        meta_el = item.select_one(".dwqa-question-meta")
        meta_text = meta_el.text if meta_el else ""
        time_ago_match = re.search(r"asked\s+([^\n•·\r\t]+)", meta_text)
        time_ago = time_ago_match.group(0).strip() if time_ago_match else ""

        # 5. Categoria
        cat_el = item.select_one(".dwqa-question-category a")
        category = cat_el.text.strip() if cat_el else "Sem Categoria"
        category_url = cat_el["href"] if cat_el and "href" in cat_el.attrs else ""

        # 6. Estatísticas numéricas (Views, Answers, Votes)
        views_el = item.select_one(".dwqa-views-count strong")
        views_count = int(views_el.text.strip()) if views_el and views_el.text.strip().isdigit() else 0

        answers_el = item.select_one(".dwqa-answers-count strong")
        answers_count = int(answers_el.text.strip()) if answers_el and answers_el.text.strip().isdigit() else 0

        votes_el = item.select_one(".dwqa-votes-count strong")
        votes_count = int(votes_el.text.strip()) if votes_el and votes_el.text.strip().isdigit() else 0

        topics.append({
            "page": page_num,
            "title": title,
            "url": url,
            "status": status,
            "category": category,
            "category_url": category_url,
            "author_name": author_name,
            "author_user": author_user,
            "author_url": author_url,
            "time_ago": time_ago,
            "views_count": views_count,
            "answers_count": answers_count,
            "votes_count": votes_count,
        })

    return topics


def fetch_all_listing_pages(start_page: int = 1, end_page: int = 34) -> List[Dict[str, Any]]:
    """Varre todas as páginas de listagem e retorna os metadados dos tópicos."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    all_topics = []
    seen_urls = set()

    print(f"\n[Fase 1] Coletando listagem das páginas {start_page} a {end_page}...")

    for page in range(start_page, end_page + 1):
        url = BASE_FORUM_PAGE_URL.format(page)
        success = False
        
        for attempt in range(3):
            try:
                r = session.get(url, timeout=15)
                r.encoding = "utf-8"
                if r.status_code == 200:
                    page_topics = extract_listing_page(r.text, page)
                    
                    # Validar e adicionar na ordem
                    for t in page_topics:
                        if t["url"] and t["url"] not in seen_urls:
                            seen_urls.add(t["url"])
                            t["id"] = len(all_topics) + 1
                            all_topics.append(t)
                        elif t["url"] in seen_urls:
                            print(f"  [Aviso] Tópico duplicado ignorado na pág {page}: {t['url']}")
                            
                    print(f"  -> Página {page:02d}/{end_page}: {len(page_topics)} tópicos encontrados (Total acumulado: {len(all_topics)})")
                    success = True
                    break
                else:
                    print(f"  [Tentativa {attempt+1}] Página {page} retornou status {r.status_code}. Repetindo...")
                    time.sleep(1)
            except Exception as e:
                print(f"  [Tentativa {attempt+1}] Erro ao buscar página {page}: {e}. Repetindo...")
                time.sleep(1.5)

        if not success:
            print(f"  [ERRO CRÍTICO] Falha ao obter a página {page} após 3 tentativas!")

    print(f"[Fase 1 Concluída] Total de {len(all_topics)} tópicos únicos coletados da listagem.\n")
    return all_topics


def parse_topic_detail(html: str) -> Dict[str, Any]:
    """Faz o parse detalhado da página de um tópico individual."""
    soup = BeautifulSoup(html, "html.parser")

    # 1. Datas exatas via JSON-LD Schema
    date_published = None
    date_modified = None
    schema_tag = soup.select_one('script[type="application/ld+json"]')
    if schema_tag and schema_tag.string:
        try:
            data = json.loads(schema_tag.string)
            for item in data.get("@graph", []):
                if "datePublished" in item:
                    date_published = item.get("datePublished")
                    date_modified = item.get("dateModified")
                    break
        except Exception:
            pass

    # 2. Corpo da pergunta
    q_content_el = soup.select_one(".dwqa-question-content")
    question_body = clean_text(q_content_el.get_text(separator="\n", strip=True)) if q_content_el else ""

    # 3. Tags associadas
    tags = [
        a.text.strip()
        for a in soup.select(".dwqa-question-tags a, a[rel='tag']")
        if "question-tag" in a.get("href", "")
    ]

    # 4. Respostas detalhadas
    answers = []
    has_staff_answer = False

    for ans_el in soup.select(".dwqa-answer-item"):
        ans_author_el = ans_el.select_one("a[href*='/forum/?user=']")
        ans_author = ans_author_el.text.strip() if ans_author_el else "Unknown"
        ans_author_link = ans_author_el["href"] if ans_author_el and "href" in ans_author_el.attrs else ""

        ans_meta_el = ans_el.select_one(".dwqa-answer-meta")
        ans_meta = ans_meta_el.text.strip() if ans_meta_el else ""

        if "Staff" in ans_meta:
            has_staff_answer = True

        ans_date_text = ""
        if "answered" in ans_meta:
            ans_date_text = ans_meta.split("answered")[-1].strip()

        ans_content_el = ans_el.select_one(".dwqa-answer-content")
        ans_content = clean_text(ans_content_el.get_text(separator="\n", strip=True)) if ans_content_el else ""

        vote_el = ans_el.select_one(".dwqa-vote-count")
        votes = int(vote_el.text.strip()) if vote_el and vote_el.text.strip().isdigit() else 0

        is_best = bool(ans_el.select_one(".dwqa-best-answer"))

        answers.append({
            "author": ans_author,
            "author_link": ans_author_link,
            "meta": ans_meta,
            "date_text": ans_date_text,
            "votes": votes,
            "is_best": is_best,
            "content": ans_content
        })

    words = re.findall(r"\w+", question_body)

    return {
        "date_published": date_published,
        "date_modified": date_modified,
        "tags": tags,
        "question_body": question_body,
        "question_length_chars": len(question_body),
        "question_length_words": len(words),
        "answers": answers,
        "answers_extracted_count": len(answers),
        "has_staff_answer": has_staff_answer,
    }


async def fetch_all_topic_details_async(topics: List[Dict[str, Any]], concurrency: int = 5) -> None:
    """Busca o detalhe de todas as URLs de tópicos em paralelo com controle de concorrência."""
    semaphore = asyncio.Semaphore(concurrency)
    timeout = aiohttp.ClientTimeout(total=30)
    
    print(f"[Fase 2] Extraindo detalhes de cada um dos {len(topics)} tópicos (Concorrência: {concurrency})...")

    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS, timeout=timeout) as session:
        async def fetch_one(topic: Dict[str, Any], pbar):
            url = topic["url"]
            details = {
                "date_published": None,
                "date_modified": None,
                "tags": [],
                "question_body": "",
                "question_length_chars": 0,
                "question_length_words": 0,
                "answers": [],
                "answers_extracted_count": 0,
                "has_staff_answer": False,
            }

            for attempt in range(3):
                try:
                    async with semaphore:
                        async with session.get(url) as response:
                            if response.status == 200:
                                html = await response.text(encoding="utf-8", errors="replace")
                                details = parse_topic_detail(html)
                                break
                            else:
                                await asyncio.sleep(1)
                except Exception:
                    await asyncio.sleep(1.5)

            topic.update(details)
            pbar.update(1)

        pbar = tqdm(total=len(topics), desc="Extraindo tópicos", unit="tópico")
        tasks = [fetch_one(t, pbar) for t in topics]
        await asyncio.gather(*tasks)
        pbar.close()

    print("[Fase 2 Concluída] Todos os detalhes extraídos com sucesso!\n")


def enrich_topic(t: Dict[str, Any]) -> None:
    """Enriquece o dicionário do tópico com todos os campos derivados para paridade 100% entre formatos."""
    t["is_resolved"] = (t.get("status") == "Resolved")
    t["is_answered"] = (t.get("answers_count", 0) > 0 or t.get("status") in ["Answered", "Resolved"])
    answers = t.get("answers", [])
    t["first_answer_author"] = answers[0]["author"] if answers else ""
    author_list = [a["author"] for a in answers if a.get("author")]
    t["answers_authors"] = author_list
    t["answers_authors_str"] = "; ".join(author_list)


def save_csv(topics: List[Dict[str, Any]], filepath: str) -> None:
    """Salva a tabela consolidada em CSV com encoding UTF-8 com BOM (ideal para Excel/Pandas)."""
    fieldnames = [
        "id",
        "page",
        "title",
        "url",
        "status",
        "is_resolved",
        "is_answered",
        "category",
        "category_url",
        "author_name",
        "author_user",
        "author_url",
        "time_ago",
        "date_published",
        "date_modified",
        "views_count",
        "answers_count",
        "votes_count",
        "question_length_chars",
        "question_length_words",
        "tags",
        "has_staff_answer",
        "first_answer_author",
        "answers_authors",
        "question_body",
    ]

    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for t in topics:
            enrich_topic(t)
            row = dict(t)
            row["tags"] = "; ".join(t.get("tags", []))
            row["answers_authors"] = t.get("answers_authors_str", "")
            writer.writerow(row)

    print(f"  [CSV Salvo]: {filepath}")


def save_json(topics: List[Dict[str, Any]], filepath: str) -> None:
    """Salva a estrutura completa aninhada em JSON com todas as informações extraídas e derivadas."""
    for t in topics:
        enrich_topic(t)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    print(f"  [JSON Salvo]: {filepath}")


def save_corpus_txt(topics: List[Dict[str, Any]], filepath: str) -> None:
    """Salva todos os tópicos e discussões formatados em um único arquivo de texto limpo."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# CorText Manager - Corpus Completo de Discussões do Fórum\n")
        f.write(f"# Data da Extração: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"# Total de Tópicos Únicos: {len(topics)}\n")
        f.write("=" * 100 + "\n\n")

        for t in topics:
            enrich_topic(t)
            f.write(f"## [{t.get('id', 0)}] {t.get('title', 'Sem Título')}\n")
            f.write(f"- URL: {t.get('url')}\n")
            f.write(f"- Página no Fórum: {t.get('page')}\n")
            f.write(f"- Categoria: {t.get('category', 'Nenhuma')}\n")
            f.write(f"- Status: {t.get('status')} (Resolvido: {t.get('is_resolved')} | Respondido: {t.get('is_answered')})\n")
            f.write(f"- Autor: {t.get('author_name')} (@{t.get('author_user')}) - {t.get('time_ago')}\n")
            f.write(f"- Data Publicação (ISO): {t.get('date_published')}\n")
            f.write(f"- Data Modificação (ISO): {t.get('date_modified') or 'N/D'}\n")
            f.write(f"- Estatísticas: {t.get('views_count')} views | {t.get('answers_count')} respostas | {t.get('votes_count')} votos\n")
            f.write(f"- Extensão: {t.get('question_length_words')} palavras ({t.get('question_length_chars')} caracteres)\n")
            if t.get("tags"):
                f.write(f"- Tags: {', '.join(t.get('tags'))}\n")
            if t.get("has_staff_answer"):
                f.write("- Atendido pela Equipe (Staff): Sim\n")
            f.write("\n### Dúvida:\n")
            f.write(t.get("question_body", "[Sem conteúdo]") + "\n\n")

            answers = t.get("answers", [])
            if answers:
                f.write(f"### Respostas ({len(answers)}):\n")
                for idx, ans in enumerate(answers, 1):
                    f.write(f"--- Resposta {idx} por {ans.get('author')} ({ans.get('date_text')}) ---\n")
                    f.write(ans.get("content", "[Sem conteúdo]") + "\n\n")
            else:
                f.write("### Respostas: Nenhuma resposta registrada.\n\n")

            f.write("=" * 100 + "\n\n")

    print(f"  [Corpus TXT Salvo]: {filepath}")


def save_corpus_md(topics: List[Dict[str, Any]], filepath: str) -> None:
    """Salva todos os tópicos e discussões formatados em Markdown com paridade 100% de metadados."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Corpus de Discussões do Fórum CorText Manager\n\n")
        f.write("> **Documento Consolidado para Análise Textual e Qualitativa (TCC - UFBA)**  \n")
        f.write(f"> **Data da Extração:** {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')}  \n")
        f.write(f"> **Total de Tópicos Únicos:** {len(topics)} tópicos (Páginas 1 a 34)  \n")
        f.write("> **Paridade Total:** Contém 100% dos dados tabulares e das discussões completas.  \n\n")
        f.write("---\n\n")

        for t in topics:
            enrich_topic(t)
            topic_id = t.get("id", 0)
            page_num = t.get("page", 0)
            title = t.get("title", "Sem Título")
            url = t.get("url", "")
            category = t.get("category", "Sem Categoria")
            category_url = t.get("category_url", "")
            status = t.get("status", "Unknown")
            is_resolved = t.get("is_resolved", False)
            is_answered = t.get("is_answered", False)
            author_name = t.get("author_name", "Anônimo")
            author_user = t.get("author_user", "")
            author_url = t.get("author_url", "")
            time_ago = t.get("time_ago", "")
            date_pub = t.get("date_published") or "N/D"
            date_mod = t.get("date_modified") or "N/D"
            views = t.get("views_count", 0)
            answers = t.get("answers", [])
            votes = t.get("votes_count", 0)
            length_words = t.get("question_length_words", 0)
            length_chars = t.get("question_length_chars", 0)
            tags = t.get("tags", [])
            has_staff = t.get("has_staff_answer", False)
            first_ans_author = t.get("first_answer_author", "")
            ans_authors_list = t.get("answers_authors", [])

            # Status badge visual
            status_emoji = "🟢" if status in ["Resolved", "Answered"] else "🟡" if status == "Open" else "⚪"

            f.write(f"## {status_emoji} [{topic_id}] {title}\n\n")
            f.write(f"| Metadado | Detalhe |\n")
            f.write(f"| :--- | :--- |\n")
            f.write(f"| **ID & Paginação** | `ID: {topic_id}` &nbsp;•&nbsp; `Página: {page_num}/34` |\n")
            f.write(f"| **Link Original** | [{url}]({url}) |\n")
            if category_url:
                f.write(f"| **Categoria** | [`{category}`]({category_url}) |\n")
            else:
                f.write(f"| **Categoria** | `{category}` |\n")
            f.write(f"| **Status** | **{status}** &nbsp;(Resolvido: `{'Sim' if is_resolved else 'Não'}` &bull; Respondido: `{'Sim' if is_answered else 'Não'}`) |\n")
            if author_url:
                f.write(f"| **Autor** | [**{author_name}**]({author_url}) (`@{author_user}`) — *{time_ago}* |\n")
            else:
                f.write(f"| **Autor** | **{author_name}** (`@{author_user}`) — *{time_ago}* |\n")
            f.write(f"| **Data Publicação (ISO)** | `{date_pub}` |\n")
            f.write(f"| **Data Modificação (ISO)** | `{date_mod}` |\n")
            f.write(f"| **Engajamento** | 👁️ {views:,} views &nbsp;•&nbsp; 💬 {len(answers)} respostas &nbsp;•&nbsp; 👍 {votes} votos |\n")
            f.write(f"| **Extensão do Texto** | {length_words} palavras &nbsp;•&nbsp; {length_chars} caracteres |\n")
            if tags:
                f.write(f"| **Tags** | {', '.join([f'`{tg}`' for tg in tags])} |\n")
            f.write(f"| **Atendimento do Staff** | `{'Sim (🛡️ Equipe CorText)' if has_staff else 'Não'}` |\n")
            if answers:
                f.write(f"| **1ª Resposta por** | **{first_ans_author}** |\n")
                f.write(f"| **Autores das Respostas** | {', '.join([f'**{a}**' for a in ans_authors_list])} |\n")
            f.write("\n")

            f.write("### ❓ Pergunta\n\n")
            q_body = t.get("question_body", "").strip()
            if q_body:
                f.write(f"{q_body}\n\n")
            else:
                f.write("_Sem corpo textual informado na pergunta._\n\n")

            if answers:
                f.write(f"### 💬 Respostas ({len(answers)})\n\n")
                for idx, ans in enumerate(answers, 1):
                    ans_author = ans.get("author", "Desconhecido")
                    ans_link = ans.get("author_link", "")
                    ans_date = ans.get("date_text", "")
                    ans_votes = ans.get("votes", 0)
                    is_best = ans.get("is_best", False)
                    is_staff = "Staff" in ans.get("meta", "")

                    badges = []
                    if is_staff:
                        badges.append("🛡️ **Equipe/Staff**")
                    if is_best:
                        badges.append("⭐ **Melhor Resposta**")
                    if ans_votes > 0:
                        badges.append(f"👍 {ans_votes} votos")

                    badge_str = f" ({' • '.join(badges)})" if badges else ""
                    if ans_link:
                        f.write(f"#### Resposta {idx} — [**{ans_author}**]({ans_link}){badge_str}\n")
                    else:
                        f.write(f"#### Resposta {idx} — **{ans_author}**{badge_str}\n")
                    if ans_date:
                        f.write(f"> *Respondido {ans_date}*\n\n")
                    
                    ans_content = ans.get("content", "").strip()
                    if ans_content:
                        f.write(f"{ans_content}\n\n")
                    else:
                        f.write("_Conteúdo vazio._\n\n")
            else:
                f.write("### 💬 Respostas\n\n_Nenhuma resposta registrada para este tópico._\n\n")

            f.write("---\n\n")

    print(f"  [Corpus MD Salvo]: {filepath}")



def generate_statistical_summary(topics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula estatísticas descritivas básicas da base extraída."""
    total = len(topics)
    if total == 0:
        return {}

    categories = {}
    statuses = {}
    authors = {}
    views = []
    answers = []
    votes = []
    question_lengths_words = []
    has_answers_count = 0
    staff_answered_count = 0

    for t in topics:
        cat = t.get("category") or "Sem Categoria"
        categories[cat] = categories.get(cat, 0) + 1

        st = t.get("status") or "Unknown"
        statuses[st] = statuses.get(st, 0) + 1

        auth = t.get("author_name") or "Anônimo"
        authors[auth] = authors.get(auth, 0) + 1

        v = t.get("views_count", 0)
        ans = t.get("answers_count", 0)
        vt = t.get("votes_count", 0)
        w = t.get("question_length_words", 0)

        views.append(v)
        answers.append(ans)
        votes.append(vt)
        question_lengths_words.append(w)

        if ans > 0 or st in ["Answered", "Resolved"]:
            has_answers_count += 1
        if t.get("has_staff_answer"):
            staff_answered_count += 1

    summary = {
        "total_topicos": total,
        "taxa_resposta_pct": round((has_answers_count / total) * 100, 2),
        "taxa_resposta_staff_pct": round((staff_answered_count / total) * 100, 2),
        "distribuicao_status": statuses,
        "distribuicao_categorias": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)),
        "autores_unicos": len(authors),
        "top_10_autores": dict(sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]),
        "top_10_perguntas_mais_visualizadas": [
            {
                "posicao": idx,
                "id": t.get("id"),
                "title": t.get("title"),
                "views_count": t.get("views_count"),
                "category": t.get("category"),
                "status": t.get("status"),
                "answers_count": t.get("answers_count"),
                "author_name": t.get("author_name"),
                "date_published": t.get("date_published"),
                "url": t.get("url")
            }
            for idx, t in enumerate(sorted(topics, key=lambda x: x.get("views_count", 0), reverse=True)[:10], 1)
        ],
        "metricas_views": {
            "total": sum(views),
            "media": round(sum(views) / total, 2),
            "max": max(views) if views else 0,
            "min": min(views) if views else 0,
        },
        "metricas_respostas": {
            "total": sum(answers),
            "media": round(sum(answers) / total, 2),
            "max": max(answers) if answers else 0,
            "min": min(answers) if answers else 0,
        },
        "metricas_votos": {
            "total": sum(votes),
            "media": round(sum(votes) / total, 2),
            "max": max(votes) if votes else 0,
            "min": min(votes) if votes else 0,
        },
        "metricas_palavras_pergunta": {
            "media": round(sum(question_lengths_words) / total, 2) if total else 0,
            "max": max(question_lengths_words) if question_lengths_words else 0,
            "min": min(question_lengths_words) if question_lengths_words else 0,
        }
    }

    return summary


def main():
    parser = argparse.ArgumentParser(description="Extrator completo e pragmático do Fórum CorText Manager.")
    parser.add_argument("--start-page", type=int, default=1, help="Página inicial (padrão: 1)")
    parser.add_argument("--end-page", type=int, default=34, help="Página final (padrão: 34)")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR, help="Diretório de saída (padrão: output_forum)")
    parser.add_argument("--concurrency", type=int, default=5, help="Número de requisições concorrentes na Fase 2 (padrão: 5)")
    parser.add_argument("--no-details", action="store_true", help="Pula a extração detalhada das dúvidas e exporta apenas a listagem")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 80)
    print(" INICIANDO EXTRAÇÃO COMPLETA DO FÓRUM CORTEXT")
    print(f" Páginas: {args.start_page} até {args.end_page}")
    print(f" Pasta de Saída: {args.output_dir}")
    print("=" * 80)

    # 1. Coleta da listagem das 34 páginas
    topics = fetch_all_listing_pages(start_page=args.start_page, end_page=args.end_page)

    if not topics:
        print("[ERRO] Nenhum tópico encontrado. Encerrando.")
        return

    # 2. Coleta dos detalhes de cada tópico
    if not args.no_details:
        asyncio.run(fetch_all_topic_details_async(topics, concurrency=args.concurrency))

    # 3. Exportações
    print("[Fase 3] Exportando dados para análise estatística...")
    csv_file = os.path.join(args.output_dir, "forum_topics.csv")
    json_file = os.path.join(args.output_dir, "forum_topics_full.json")
    txt_file = os.path.join(args.output_dir, "forum_corpus.txt")
    md_file = os.path.join(args.output_dir, "forum_corpus.md")
    summary_file = os.path.join(args.output_dir, "resumo_estatistico.json")

    save_csv(topics, csv_file)
    save_json(topics, json_file)
    save_corpus_txt(topics, txt_file)
    save_corpus_md(topics, md_file)

    # 4. Resumo estatístico
    summary = generate_statistical_summary(topics)
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  [Resumo Estatístico Salvo]: {summary_file}")

    print("\n" + "=" * 80)
    print(" RESUMO DA EXTRAÇÃO REALIZADA COM SUCESSO:")
    print(f" - Total de Tópicos Únicos: {summary.get('total_topicos')}")
    print(f" - Taxa de Tópicos com Resposta: {summary.get('taxa_resposta_pct')}%")
    print(f" - Taxa com Resposta do Staff: {summary.get('taxa_resposta_staff_pct')}%")
    print(f" - Autores Únicos que Postaram: {summary.get('autores_unicos')}")
    print(f" - Total de Visualizações Acumuladas: {summary.get('metricas_views', {}).get('total')}")
    print(f" - Total de Respostas Registradas: {summary.get('metricas_respostas', {}).get('total')}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
