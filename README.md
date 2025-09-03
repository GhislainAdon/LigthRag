<div align="center">
  
  <a href="https://vectify.ai/pageindex" target="_blank">
    <img src="https://github.com/user-attachments/assets/46201e72-675b-43bc-bfbd-081cc6b65a1d" alt="PageIndex Banner" />
  </a>
  
  <br/>
  <br/>

  <p align="center"><i>Reasoning-based RAG&nbsp; ✧ &nbsp;No Vector DB&nbsp; ✧ &nbsp;No Chunking&nbsp; ✧ &nbsp;Human-like Retrieval</i></p>

<p align="center">
  <a href="https://vectify.ai">🏠 Homepage</a>&nbsp; • &nbsp;
  <a href="https://dash.pageindex.ai">🖥️ Dashboard</a>&nbsp; • &nbsp;
  <a href="https://docs.pageindex.ai/quickstart">📚 API Docs</a>&nbsp; • &nbsp;
  <a href="https://discord.com/invite/VuXuf29EUj">💬 Discord</a>&nbsp; • &nbsp;
  <a href="https://ii2abc2jejf.typeform.com/to/tK3AXl8T">✉️ Contact</a>&nbsp;
</p>

<p align="center">
  <a href="https://github.com/VectifyAI/PageIndex/stargazers">
    <img src="https://img.shields.io/github/stars/VectifyAI/PageIndex?style=for-the-badge&logo=github&label=⭐%20Star%20Us" alt="Star us on GitHub" />
  </a>
  <a href="https://twitter.com/VectifyAI">
    <img src="https://img.shields.io/badge/Follow%20Us-000000?style=for-the-badge&logo=x&logoColor=white" alt="Follow us on X" />
  </a>
</p>

</div>

---

#  📄 Introduction to PageIndex

Are you frustrated with vector database retrieval accuracy for long professional documents? Traditional vector-based RAG relies on semantic *similarity* rather than true *relevance*. But **similarity ≠ relevance** — what we truly need in retrieval is **relevance**, and that requires **reasoning**. When working with professional documents that demand domain expertise and multi-step reasoning, similarity search often falls short.

Inspired by AlphaGo, we propose [PageIndex](https://vectify.ai/pageindex), a **reasoning-based RAG** system that simulates how **human experts** navigate and extract knowledge from long documents through **tree search**, enabling LLMs to *think* and *reason* their way to the most relevant document sections. It performs retrieval in two steps:

1. Generate a "Table-of-Contents" **tree structure index** of documents
2. Perform reasoning-based retrieval through **tree search**

<div align="center">
    <img src="https://docs.pageindex.ai/images/cookbook/vectorless-rag.png" width="90%">
</div>

### 💡 Features 

Compared to traditional vector-based RAG, PageIndex features:
- **No Vectors Needed**: Uses document structure and LLM reasoning for retrieval.
- **No Chunking Needed**: Documents are organized into natural sections, not artificial chunks.
- **Human-like Retrieval**: Simulates how human experts navigate and extract knowledge from complex documents.
- **Transparent Retrieval Process**: Retrieval based on reasoning — say goodbye to approximate vector search ("vibe retrieval").

PageIndex powers a reasoning-based RAG system that achieved [98.7% accuracy](https://github.com/VectifyAI/Mafin2.5-FinanceBench) on FinanceBench, showing state-of-the-art performance in professional document analysis (see our [blog post](https://vectify.ai/blog/Mafin2.5) for details).

### 🚀 Deployment Options
- 🛠️ Self-host — run locally with this open-source repo
- ☁️ **[Cloud Service](https://dash.pageindex.ai/)** — try instantly with our 🖥️ [Dashboard](https://dash.pageindex.ai/) or 🔌 [API](https://docs.pageindex.ai/quickstart), no setup required

### ⚡ Quick Hands-on

Check out this simple [*Vectorless RAG Notebook*](https://github.com/VectifyAI/PageIndex/blob/main/cookbook/pageindex_RAG_simple.ipynb) — a minimal, hands-on, reasoning-based RAG pipeline using **PageIndex**.
<p align="center">
<a href="https://colab.research.google.com/github/VectifyAI/PageIndex/blob/main/cookbook/pageindex_RAG_simple.ipynb">
    <img src="https://img.shields.io/badge/Open_In_Colab-Vectorless_RAG_With_PageIndex-orange?style=for-the-badge&logo=googlecolab" alt="Open in Colab"/>
  </a>
</p>

---

# 📦 PageIndex Tree Structure
PageIndex can transform lengthy PDF documents into a semantic **tree structure**, similar to a _"table of contents"_ but optimized for use with Large Language Models (LLMs). It's ideal for: financial reports, regulatory filings, academic textbooks, legal or technical manuals, and any document that exceeds LLM context limits.

Here is an example output. See more [example documents](https://github.com/VectifyAI/PageIndex/tree/main/docs) and [generated trees](https://github.com/VectifyAI/PageIndex/tree/main/results).

```
...
{
  "title": "Financial Stability",
  "node_id": "0006",
  "start_index": 21,
  "end_index": 22,
  "summary": "The Federal Reserve ...",
  "nodes": [
    {
      "title": "Monitoring Financial Vulnerabilities",
      "node_id": "0007",
      "start_index": 22,
      "end_index": 28,
      "summary": "The Federal Reserve's monitoring ..."
    },
    {
      "title": "Domestic and International Cooperation and Coordination",
      "node_id": "0008",
      "start_index": 28,
      "end_index": 31,
      "summary": "In 2023, the Federal Reserve collaborated ..."
    }
  ]
}
...
```

 You can either generate the PageIndex tree structure with this open-source repo or try our ☁️ **[Cloud Service](https://dash.pageindex.ai/)** — instantly accessible via our 🖥️ [Dashboard](https://dash.pageindex.ai/) or 🔌 [API](https://docs.pageindex.ai/quickstart), with no setup required.

---

# 🚀 Package Usage

You can follow these steps to generate a PageIndex tree from a PDF document.

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Set your OpenAI API key

Create a `.env` file in the root directory and add your API key:

```bash
CHATGPT_API_KEY=your_openai_key_here
```

### 3. Run PageIndex on your PDF

```bash
python3 run_pageindex.py --pdf_path /path/to/your/document.pdf
```

You can customize the processing with additional optional arguments:

```
--model                 OpenAI model to use (default: gpt-4o-2024-11-20)
--toc-check-pages       Pages to check for table of contents (default: 20)
--max-pages-per-node    Max pages per node (default: 10)
--max-tokens-per-node   Max tokens per node (default: 20000)
--if-add-node-id        Add node ID (yes/no, default: yes)
--if-add-node-summary   Add node summary (yes/no, default: no)
--if-add-doc-description Add doc description (yes/no, default: yes)
```


---

# ☁️ Improved Tree Generation with PageIndex OCR

This repo is designed for generating PageIndex tree structure for simple PDFs, but many real-world use cases involve complex PDFs that are hard to parsed by classic python tools. However, extracting high-quality text from PDF documents remains a non-trivial challenge. Most OCR tools only extract page-level content, losing the broader document context and hierarchy.

To address this, we introduced PageIndex OCR — the first long-context OCR model designed to preserve the global structure of documents. PageIndex OCR significantly outperforms other leading OCR tools, such as those from Mistral and Contextual AI, in recognizing true hierarchy and semantic relationships across document pages.

- Experience next-level OCR quality with PageIndex OCR at our [Dashboard](https://dash.pageindex.ai/).
- Integrate seamlessly PageIndex OCR into your stack via our [API](https://docs.pageindex.ai/quickstart).

<p align="center">
  <img src="https://github.com/user-attachments/assets/eb35d8ae-865c-4e60-a33b-ebbd00c41732" width="90%">
</p>

---

# 📈 Case Study: Mafin 2.5 on FinanceBench

[Mafin 2.5](https://vectify.ai/mafin) is a state-of-the-art reasoning-based RAG model designed specifically for financial document analysis. Powered by **PageIndex**, it achieved a market-leading [**98.7% accuracy**](https://vectify.ai/blog/Mafin2.5) on the [FinanceBench](https://arxiv.org/abs/2311.11944) benchmark — significantly outperforming traditional vector-based RAG systems.

PageIndex's hierarchical indexing enabled precise navigation and extraction of relevant content from complex financial reports, such as SEC filings and earnings disclosures.

👉 See the full [benchmark results](https://github.com/VectifyAI/Mafin2.5-FinanceBench) and our [blog post](https://vectify.ai/blog/Mafin2.5) for detailed comparisons and performance metrics.

<div align="center">
  <a href="https://github.com/VectifyAI/Mafin2.5-FinanceBench">
    <img src="https://github.com/user-attachments/assets/571aa074-d803-43c7-80c4-a04254b782a3" width="90%">
  </a>
</div>

---

# 🔎 Learn More about PageIndex

See the [Tutorials](https://docs.pageindex.ai/doc-search) for step-by-step guides, including Document Search and Tree Search.

Check out the [Cookbook](https://docs.pageindex.ai/cookbook/vectorless-rag-pageindex) for practical recipes and advanced use cases.

Refer to the [API Documentation](https://docs.pageindex.ai/quickstart) for integration details and options.

# ⭐ Support Us

Leave a star if you like our project — thank you!  

<p align="center">
  <img src="https://github.com/user-attachments/assets/eae4ff38-48ae-4a7c-b19f-eab81201d794" width="75%">
</p>

© 2025 [Vectify AI](https://vectify.ai)
