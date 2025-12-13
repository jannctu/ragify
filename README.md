# PDF to Knowledge Converter

A simple yet powerful tool to convert PDF documents into clean, structured markdown files ready for RAG (Retrieval-Augmented Generation) or AI applications. Uses GPT-4o-mini Vision API to extract and restructure content from PDF pages.

## 🚀 Features

- **PDF to Image Conversion**: Converts each PDF page into high-quality images
- **AI-Powered Extraction**: Uses GPT-4o-mini Vision to extract and clean content
- **Structured Markdown Output**: Generates clean, well-formatted markdown with:
  - Proper headings and subheadings
  - Bullet points and numbered lists
  - Fixed typos and improved readability
- **Dual Output Format**:
  - Individual markdown files per page (`document_page_001.md`)
  - Combined markdown file (`document_ALL.md`)
- **RAG-Ready**: Output is optimized for vector database ingestion

## 📋 Prerequisites

### System Requirements

- **Python 3.7+**
- **Poppler**: Required for PDF processing
  - **macOS**: `brew install poppler`
  - **Ubuntu/Debian**: `sudo apt-get install poppler-utils`
  - **Windows**: Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases/)

### API Key

- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pdf-to-knowledge.git
   cd pdf-to-knowledge
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 📖 Usage

### Basic Usage

1. Place your PDF file in the `files/` directory
2. Update the `pdf_file` variable in `main.py`:
   ```python
   pdf_file = "files/your-document.pdf"
   ```
3. Run the script:
   ```bash
   python main.py
   ```

### Output

The processed files will be saved in the `outputs/` directory:
- `document_page_001.md` - Individual page files
- `document_page_002.md`
- ...
- `document_ALL.md` - All pages combined

### Example Output Structure

```
outputs/
├── Indonesia-Salary-Guide-2025_page_001.md
├── Indonesia-Salary-Guide-2025_page_002.md
├── ...
└── Indonesia-Salary-Guide-2025_ALL.md
```

## 🎯 Use Cases

- **Building RAG Applications**: Pre-process documents for vector databases
- **Knowledge Base Creation**: Convert documentation into searchable markdown
- **Document Digitization**: Transform scanned PDFs into structured text
- **Content Migration**: Extract and clean content from legacy PDFs

## 🔧 Configuration

### Adjust DPI Quality
Higher DPI = better quality but slower processing:
```python
images = pdf_to_images(pdf_path, dpi=300)  # default is 200
```

### Customize LLM Instructions
Edit the `user_instructions` in `call_llm_vision()` function to change extraction behavior.

### Change Output Model
Switch to a different OpenAI model:
```python
model="gpt-4o",  # or "gpt-4-vision-preview"
```

## 📦 Dependencies

- `openai==1.57.4` - OpenAI API client
- `python-dotenv==1.0.1` - Environment variable management
- `pdf2image==1.17.0` - PDF to image conversion
- `Pillow==10.4.0` - Image processing

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

This project is open source and available under the MIT License.

## ⚠️ Notes

- Processing time depends on PDF size and OpenAI API response time
- Costs are based on OpenAI API usage (GPT-4o-mini vision)
- Large PDFs may take several minutes to process
- Ensure stable internet connection for API calls

## 🙏 Acknowledgments

Built with:
- [OpenAI GPT-4o-mini](https://openai.com/)
- [pdf2image](https://github.com/Belval/pdf2image)
- [Poppler](https://poppler.freedesktop.org/)

---

Made with ❤️ for better document processing
