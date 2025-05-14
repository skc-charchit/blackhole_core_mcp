# 🚀 Blackhole Core Project

A modular AI-powered framework for ingesting multimodal data (images, PDFs, text), processing them via agents and pipelines, and storing structured insights into MongoDB.

---

## 📖 Table of Contents

- [📂 blackhole_core/](blackhole_core/README.md)
- [📂 blackhole_core/data_source/](blackhole_core/data_source/README.md)
- [📂 data/multimodal/](data/multimodal/README.md)
- [📂 data/pipelines/](data/pipelines/README.md)
- [📂 adapter/](adapter/README.md)
- [📂 api/](api/README.md)

---

## 📦 Project Structure

--- plain text

project_root/
├── adapter/
├── api/
├── blackhole_core/
│ └── data_source/
├── data/
│ ├── multimodal/
│ └── pipelines/
├── .env
├── .gitignore
├── Dockerfile
├── docker-compose.yaml
├── LICENSE
├── README.md
├── requirements.txt

---


---

## 📜 Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure MongoDB is running (via docker-compose or locally)
docker-compose up -d


# Run the demo pipeline to process a sample PDF and image
python data/pipelines/blackhole_demo.py



---

## 📂 `blackhole_core/README.md`

```markdown
# 📦 blackhole_core

This module contains essential backend scripts for handling data sources and MongoDB integration.

## 📜 Scripts

- **data_source/mongodb.py** — Establishes and manages MongoDB connection for data storage.

---

## 📈 Bash Commands

```bash
# Test MongoDB connection script
python blackhole_core/data_source/mongodb.py



---

## 📂 `blackhole_core/data_source/README.md`

```markdown
# 📦 data_source

Holds sample archives and database connection scripts.

## 📜 Files

- **mongodb.py** — Connects to MongoDB using `.env` configuration.
- **sample_archive.csv** — Sample CSV archive used for offline lookup by agents.

---

## 📈 Bash Commands

```bash
# Run MongoDB connection check
python mongodb.py



---

## 📂 `data/multimodal/README.md`

```markdown
# 📦 data/multimodal

Multimodal processing tools for images and PDFs.

## 📜 Scripts

- **image_ocr.py** — Performs OCR on images and extracts text.
- **pdf_reader.py** — Extracts text from PDF documents.

---

## 📈 Bash Commands

```bash
# Run OCR on a sample image
python data/multimodal/image_ocr.py data/multimodal/sample_image.png

# Extract text from a PDF
python data/multimodal/pdf_reader.py data/multimodal/sample.pdf


---

## 📂 `data/pipelines/README.md`

```markdown
# 📦 data/pipelines

Main orchestration pipelines to process multimodal inputs, run agents, and store results.

## 📜 Scripts

- **blackhole_demo.py** — Loads a sample PDF and image, processes them, runs an agent on the extracted text, and stores insights into MongoDB.

---

## 📈 Bash Commands

```bash
# Run the demo pipeline
python data/pipelines/blackhole_demo.py

# 📦 api

This module will house the MCP Adapter REST API service for Blackhole Core.

## 📜 Scripts

- **mcp_adapter.py** — (To be built in STEP 6) Exposes REST API endpoints to interact with the core pipeline.

---

## 📈 Planned Bash Command (Post-STEP 6)

```bash
# Run the MCP Adapter API
python api/mcp_adapter.py
