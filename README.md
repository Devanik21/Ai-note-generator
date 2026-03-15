# AI Note Generator

![Language](https://img.shields.io/badge/Language-Python-3776AB?style=flat-square) ![Stars](https://img.shields.io/github/stars/Devanik21/Ai-note-generator?style=flat-square&color=yellow) ![Forks](https://img.shields.io/github/forks/Devanik21/Ai-note-generator?style=flat-square&color=blue) ![Author](https://img.shields.io/badge/Author-Devanik21-black?style=flat-square&logo=github) ![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

> AI Note Generator — AI-powered productivity that transforms effort into polished, professional output.

---

**Topics:** `content-generation` · `deep-learning` · `education-ai` · `generative-ai` · `large-language-models` · `lecture-summarization` · `natural-language-processing` · `nlp` · `student-productivity` · `study-material-generation`

## Overview

AI Note Generator is an LLM-powered productivity application that automates or dramatically accelerates a specific professional workflow. It combines carefully designed prompts, structured output parsing, and a clean user interface to deliver results that would take hours manually in seconds.

The application is built on a modular prompt architecture: each workflow step has a dedicated prompt template with clear instructions, output format specification, and example outputs (few-shot). This makes the LLM behaviour predictable, consistent, and easy to audit.

All generated content is presented in a structured, editable format before any export or download, allowing the user to review and refine AI output before using it. The tool is designed to augment human judgment, not replace it.

---

## Motivation

Professional content creation — writing, structuring, and polishing documents, posts, and materials — consumes enormous amounts of time that could be spent on higher-value thinking. This tool applies LLMs where they are most powerful: producing well-structured, professionally toned first drafts that humans can quickly review and finalise.

---

## Architecture

```
User input (topic, tone, parameters)
        │
  Prompt construction (template + user data)
        │
  LLM API call (GPT-4o / Gemini)
        │
  Output parsing and formatting
        │
  Edit interface → Export (PDF/DOCX/Markdown)
```

---

## Features

### AI Content Generation
LLM-powered generation of professional content tailored to specific tone, audience, and purpose parameters.

### Template Library
Pre-built prompt templates for common use cases, customisable for specific needs.

### Iterative Refinement
Regenerate individual sections or the full output with adjusted parameters without restarting from scratch.

### Tone and Style Control
Select from professional/formal, conversational, technical, creative, or concise tone profiles.

### Multi-Format Export
Export generated content as PDF, Word document, or Markdown for downstream use.

### Version Comparison
Side-by-side comparison of multiple generated versions to select the best output.

### History Management
Save and restore previous sessions, preventing loss of good outputs.

### API Backend Flexibility
Switch between OpenAI, Gemini, and other backends via environment variable.

---

## Tech Stack

| Library / Tool | Role | Why This Choice |
|---|---|---|
| **Streamlit** | UI framework | Form inputs, preview panel, download buttons |
| **OpenAI / Gemini SDK** | LLM backend | Content generation API calls |
| **python-dotenv** | Config | API key management |
| **ReportLab / python-docx** | Export | PDF and DOCX generation |
| **pandas** | History | Session storage and retrieval |

> **Key packages detected in this repo:** `streamlit` · `google-generativeai` · `pandas` · `datetime` · `markdown` · `gTTS`

---

## Getting Started

### Prerequisites

- Python 3.9+ (or Node.js 18+ for TypeScript/JS projects)
- `pip` or `npm` package manager
- Relevant API keys (see Configuration section)

### Installation

```bash
git clone https://github.com/Devanik21/Ai-note-generator.git
cd Ai-note-generator
python -m venv venv && source venv/bin/activate
pip install streamlit openai google-generativeai python-dotenv
echo 'OPENAI_API_KEY=sk-...' > .env
streamlit run app.py
```

---

## Usage

```bash
streamlit run app.py
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | `(required)` | LLM API key |
| `BACKEND` | `openai` | LLM backend: openai, gemini |
| `DEFAULT_TONE` | `professional` | Output tone: professional, conversational, technical |

> Copy `.env.example` to `.env` and populate all required values before running.

---

## Project Structure

```
Ai-note-generator/
├── README.md
├── requirements.txt
├── app.py
└── ...
```

---

## Roadmap

- [ ] Batch generation mode for multiple outputs in one run
- [ ] Template marketplace for community-contributed prompts
- [ ] Integration with Google Docs / Notion API for direct publishing
- [ ] A/B testing: generate multiple variants and rate them for preference learning
- [ ] Voice input with Whisper for hands-free content creation

---

## Contributing

Contributions, issues, and feature requests are welcome. Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'feat: add your feature'`)
4. Push to your branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please follow conventional commit messages and ensure any new code is documented.

---

## Notes

All AI-generated content should be reviewed by the user before use. LLM outputs can contain inaccuracies and should not be used without human review.

---

## Author

**Devanik Debnath**  
B.Tech, Electronics & Communication Engineering  
National Institute of Technology Agartala

[![GitHub](https://img.shields.io/badge/GitHub-Devanik21-black?style=flat-square&logo=github)](https://github.com/Devanik21)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-devanik-blue?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/devanik/)

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

*Crafted with curiosity, precision, and a belief that good software is worth building well.*
