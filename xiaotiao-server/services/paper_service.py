"""Paper processing service — URL fetching, PDF parsing, metadata extraction."""

import os
import re
import json
import uuid
import sqlite3
import asyncio
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "./db/xiaotiao.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "papers")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def extract_arxiv_id(url: str) -> str | None:
    """Extract arXiv paper ID from URL."""
    patterns = [
        r'arxiv\.org/abs/(\d+\.\d+)',
        r'arxiv\.org/pdf/(\d+\.\d+)',
        r'arxiv\.org/abs/([\w\-]+/\d+)',
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


async def fetch_arxiv_metadata(arxiv_id: str) -> dict:
    """Fetch paper metadata from arXiv API."""
    import httpx
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(api_url)
        resp.raise_for_status()

    import xml.etree.ElementTree as ET
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(resp.text)
    entry = root.find('atom:entry', ns)

    if entry is None:
        return {}

    title = entry.findtext('atom:title', '', ns).strip().replace('\n', ' ')
    abstract = entry.findtext('atom:summary', '', ns).strip()
    authors = [a.findtext('atom:name', '', ns) for a in entry.findall('atom:author', ns)]

    # Find PDF link
    pdf_url = None
    for link in entry.findall('atom:link', ns):
        if link.get('title') == 'pdf':
            pdf_url = link.get('href')

    return {
        'title': title,
        'abstract': abstract,
        'authors': json.dumps(authors),
        'arxiv_id': arxiv_id,
        'pdf_url': pdf_url or f"https://arxiv.org/pdf/{arxiv_id}.pdf",
    }


async def process_paper_url(paper_id: str, url: str):
    """Background task: fetch metadata for a paper URL and update the record."""
    conn = _connect()
    try:
        conn.execute(
            "UPDATE papers SET status='processing', updated_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), paper_id)
        )
        conn.commit()

        arxiv_id = extract_arxiv_id(url)
        if arxiv_id:
            meta = await fetch_arxiv_metadata(arxiv_id)
            if meta:
                conn.execute(
                    """UPDATE papers SET title=?, abstract=?, authors=?, arxiv_id=?,
                       pdf_url=?, status='ready', updated_at=? WHERE id=?""",
                    (meta['title'], meta['abstract'], meta['authors'],
                     meta['arxiv_id'], meta['pdf_url'],
                     datetime.utcnow().isoformat(), paper_id)
                )
                conn.commit()
                return

        # Non-arXiv URL: try generic fetch
        import httpx
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url)
            # Extract title from HTML
            title_match = re.search(r'<title>(.*?)</title>', resp.text, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else url

        conn.execute(
            "UPDATE papers SET title=?, status='ready', updated_at=? WHERE id=?",
            (title, datetime.utcnow().isoformat(), paper_id)
        )
        conn.commit()
    except Exception as e:
        conn.execute(
            "UPDATE papers SET status='failed', updated_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), paper_id)
        )
        conn.commit()
        print(f"[paper_service] Error processing {paper_id}: {e}")
    finally:
        conn.close()


def process_paper_pdf(paper_id: str, pdf_path: str):
    """Extract text from uploaded PDF and update paper record."""
    conn = _connect()
    try:
        conn.execute(
            "UPDATE papers SET status='processing', updated_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), paper_id)
        )
        conn.commit()

        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        doc.close()

        # Truncate to ~8000 words
        words = full_text.split()
        if len(words) > 8000:
            full_text = " ".join(words[:8000])

        # Extract title from first meaningful line
        lines = [l.strip() for l in full_text.split('\n') if l.strip()]
        title = lines[0][:200] if lines else os.path.basename(pdf_path)

        conn.execute(
            """UPDATE papers SET title=?, abstract=?, status='ready', updated_at=? WHERE id=?""",
            (title, full_text[:2000], datetime.utcnow().isoformat(), paper_id)
        )
        conn.commit()
    except Exception as e:
        conn.execute(
            "UPDATE papers SET status='failed', updated_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), paper_id)
        )
        conn.commit()
        print(f"[paper_service] PDF processing error {paper_id}: {e}")
    finally:
        conn.close()


def get_paper_text(paper_id: str) -> str:
    """Get the full text content of a paper for AI context."""
    conn = _connect()
    try:
        row = conn.execute("SELECT abstract, pdf_path FROM papers WHERE id=?", (paper_id,)).fetchone()
        if not row:
            return ""

        # If we have a local PDF, extract fresh text
        if row['pdf_path'] and os.path.exists(row['pdf_path']):
            try:
                import fitz
                doc = fitz.open(row['pdf_path'])
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                words = text.split()
                return " ".join(words[:8000])
            except Exception:
                pass

        # Fall back to stored abstract
        return row['abstract'] or ""
    finally:
        conn.close()
