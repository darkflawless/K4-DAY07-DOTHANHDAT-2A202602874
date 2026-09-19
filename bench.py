"""
Benchmark Runner for Lab 07 - Embedding & Vector Store.
Supports OpenAI semantic embeddings + OpenAI LLM response generation with cache.
"""

import os
import re
import csv
import sys
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
load_dotenv()

from src.models import Document
from src.store import EmbeddingStore
from src.embeddings import MockEmbedder, OpenAIEmbedder
from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, SentenceChunker, RecursiveChunker

# Định nghĩa 5 Benchmark Queries chuẩn hóa của nhóm
BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Sinh viên năm thứ mấy và cần đạt kết quả học tập thế nào để đủ điều kiện xét học bổng EVN?",
        "gold_doc_id": "hoc-bong-evn",
        "gold_keyword": "sinh viên năm thứ 3",
        "gold_answer": "Sinh viên năm thứ 3 đang theo học các ngành năng lượng, CNTT... kết quả học tập năm học 2025-2026 đạt loại giỏi trở lên, rèn luyện tốt, chưa nhận học bổng ngoài ngân sách.",
        "filter": None
    },
    {
        "id": 2,
        "query": "Thời gian nghỉ Tết Nguyên đán năm học 2025-2026 của sinh viên chính quy kéo dài từ ngày nào đến ngày nào?",
        "gold_doc_id": "ke-hoach-dao-tao-nam-hoc",
        "gold_keyword": "09/02-22/02/2026",
        "gold_answer": "Thời gian nghỉ Tết Nguyên đán từ 09/02/2026 đến 22/02/2026.",
        "filter": None
    },
    {
        "id": 3,
        "query": "Phương thức 2 của Trường ĐH Khoa học Tự nhiên năm 2026 áp dụng nhân hệ số 2 môn Toán cho những ngành nào?",
        "gold_doc_id": "phuong-thuc-xet-tuyen-hus",
        "gold_keyword": "Toán học, Toán tin, Khoa học máy tính và thông tin, Khoa học dữ liệu",
        "gold_answer": "Môn Toán nhân hệ số 2 cho các ngành: Toán học, Toán tin, Khoa học máy tính và thông tin, Khoa học dữ liệu.",
        "filter": None
    },
    {
        "id": 4,
        "query": "Chương trình trao đổi sinh viên tại Đại học Osaka kỳ Xuân 2027 có bao nhiêu chỉ tiêu và yêu cầu điểm GPA tối thiểu là bao nhiêu?",
        "gold_doc_id": "trao-doi-sinh-vien-osaka",
        "gold_keyword": "GPA từ 3,2/4,0",
        "gold_answer": "Có 03 chỉ tiêu dành cho sinh viên/học viên ĐHQGHN; yêu cầu hoàn thành ít nhất 02 học kỳ và GPA từ 3,2/4,0 trở lên.",
        "filter": None
    },
    {
        "id": 5,
        "query": "Số lượng và danh mục các chương trình đào tạo chuẩn và đặc thù của Trường Đại học Công nghệ là gì?",
        "gold_doc_id": "chuong-trinh-dao-tao-dai-hoc",
        "gold_keyword": "Công nghệ thông tin",
        "gold_answer": "Bao gồm 18 chương trình đào tạo (CNTT, CNTT CLC, Robot, Năng lượng, Cơ kỹ thuật, AI...).",
        "filter": {"audience": "student"} # Ràng buộc L3A
    }
]

CACHE_FILE = Path(".embedding_cache.json")

class CachedOpenAIEmbedder:
    """Cached OpenAI embedder to avoid redundant API calls and save quota."""
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI()
        self.cache = {}
        if CACHE_FILE.exists():
            try:
                self.cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.cache = {}

    def __call__(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if h in self.cache:
            return self.cache[h]
        res = self.client.embeddings.create(model="text-embedding-3-small", input=text)
        vec = [float(v) for v in res.data[0].embedding]
        self.cache[h] = vec
        CACHE_FILE.write_text(json.dumps(self.cache), encoding="utf-8")
        return vec

def openai_llm_fn(prompt: str) -> str:
    """Gọi OpenAI GPT-4o-mini sinh câu trả lời RAG thật sự."""
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Bạn là trợ lý giải đáp thông tin quy chế và dịch vụ của Đại học Quốc gia Hà Nội. Hãy trả lời ngắn gọn, chính xác dựa trên ngữ cảnh được cung cấp."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=250
    )
    return response.choices[0].message.content.strip()

def parse_markdown_document(path: Path) -> tuple[Dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            content = parts[2].strip()
            metadata = {}
            for line in fm_text.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip()] = val.strip().strip('"').strip("'")
            return metadata, content
    return {}, text.strip()

def load_corpus(data_dir: Path, chunker) -> List[Document]:
    documents = []
    md_files = sorted(data_dir.glob("*.md"))
    for file_path in md_files:
        meta, content = parse_markdown_document(file_path)
        doc_id = meta.get("doc_id", file_path.stem)
        chunks = chunker.chunk(content)
        for i, chunk_text in enumerate(chunks):
            doc = Document(
                id=f"{doc_id}#{i}",
                content=chunk_text,
                metadata={**meta, "doc_id": doc_id, "chunk_index": i}
            )
            documents.append(doc)
    return documents

def run_benchmark(strategy_name: str, chunker, output_file: Optional[Path] = None, use_real_api: bool = True):
    data_dir = Path("data/university")
    docs = load_corpus(data_dir, chunker)
    
    if use_real_api:
        embedder = CachedOpenAIEmbedder()
        llm = openai_llm_fn
        backend_info = "OpenAI (text-embedding-3-small + gpt-4o-mini)"
    else:
        embedder = MockEmbedder()
        llm = lambda p: "Mock Answer"
        backend_info = "MockEmbedder (MD5 hash)"

    store = EmbeddingStore(embedding_fn=embedder)
    store.add_documents(docs)
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm)

    lines = []
    lines.append("============================================================")
    lines.append(f"BENCHMARK REPORT: Chien luoc [{strategy_name}]")
    lines.append(f"Backend: {backend_info}")
    lines.append(f"Tong so chunks nap vao store: {store.get_collection_size()} chunks tu 6 files")
    lines.append("============================================================\n")

    correct_top1 = 0
    correct_top3 = 0

    for item in BENCHMARK_QUERIES:
        qid = item["id"]
        query = item["query"]
        gold_doc = item["gold_doc_id"]
        gold_kw = item["gold_keyword"]
        flt = item["filter"]

        if flt:
            results = store.search_with_filter(query, metadata_filter=flt, top_k=3)
        else:
            results = store.search(query, top_k=3)

        agent_answer = agent.answer(query, top_k=3)

        # Kiểm tra tính liên quan
        top1_hit = False
        top3_hit = False
        if results:
            if gold_doc in results[0]["id"] or gold_kw.lower() in results[0]["content"].lower():
                top1_hit = True
            for r in results:
                if gold_doc in r["id"] or gold_kw.lower() in r["content"].lower():
                    top3_hit = True
                    break

        if top1_hit: correct_top1 += 1
        if top3_hit: correct_top3 += 1

        lines.append(f"Query #{qid}: {query}")
        if flt:
            lines.append(f"  [Filter ap dung]: {flt}")
        lines.append(f"  [Gold Doc ID]: {gold_doc}")
        top1_id = results[0]['id'] if results else 'None'
        top1_score = f"{results[0]['score']:.4f}" if results else 'N/A'
        lines.append(f"  [Top-1 Doc ID]: {top1_id} (Score: {top1_score})")
        clean_content = results[0]['content'][:120].replace('\n', ' ') if results else 'None'
        lines.append(f"  [Top-1 Content Preview]: {clean_content}...")
        rel_top1 = 'CO' if top1_hit else 'KHONG'
        rel_top3 = 'CO' if top3_hit else 'KHONG'
        lines.append(f"  [Top-1 Relevant?]: {rel_top1} | [Top-3 Relevant?]: {rel_top3}")
        clean_ans = agent_answer.replace('\n', ' ')
        lines.append(f"  [Agent Answer]: {clean_ans}\n")

    lines.append("------------------------------------------------------------")
    lines.append("KET QUA TONG KET:")
    lines.append(f"  - Top-1 Accuracy: {correct_top1}/5 ({correct_top1/5*100:.1f}%)")
    lines.append(f"  - Top-3 Accuracy: {correct_top3}/5 ({correct_top3/5*100:.1f}%)")
    lines.append("------------------------------------------------------------\n")

    # A/B Test Query 5 (So sánh có filter và không filter)
    q5 = BENCHMARK_QUERIES[4]
    lines.append("=== A/B TEST REPORT (QUERY 5): Co Filter vs Khong Filter ===")
    res_no_flt = store.search(q5["query"], top_k=3)
    res_flt = store.search_with_filter(q5["query"], metadata_filter=q5["filter"], top_k=3)

    lines.append("1. Khi KHONG dung filter (Dua tren similarity thuan tuy):")
    for idx, r in enumerate(res_no_flt):
        lines.append(f"   Top-{idx+1}: {r['id']} (Audience: {r['metadata'].get('audience')}) - Score: {r['score']:.4f}")

    lines.append("2. Khi CO dung filter {'audience': 'student'}:")
    for idx, r in enumerate(res_flt):
        lines.append(f"   Top-{idx+1}: {r['id']} (Audience: {r['metadata'].get('audience')}) - Score: {r['score']:.4f}")
    lines.append("============================================================\n")

    report_text = "\n".join(lines)
    print(report_text)

    if output_file:
        output_file.write_text(report_text, encoding="utf-8")
        print(f"Da luu ket qua tai: {output_file}")

if __name__ == "__main__":
    chosen_strategy = "RecursiveChunker(chunk_size=400)"
    chunker = RecursiveChunker(chunk_size=400)
    out_path = Path("ket_qua_benchmark.txt")
    run_benchmark(chosen_strategy, chunker, output_file=out_path, use_real_api=True)
