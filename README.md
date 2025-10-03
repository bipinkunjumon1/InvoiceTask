# Invoice & Purchase Order Matching Tool

A web-based tool to automatically compare an invoice with its corresponding purchase order. It extracts key details, checks for matches, and highlights discrepancies.

## Features

-   **Upload Documents**: Accepts both PDF and common image formats for invoices and purchase orders.
-   **Intelligent Data Extraction**: Uses the Google Gemini Pro model to read and understand the documents.
-   **Hybrid Parsing Strategy**: 
    -   Prioritizes accurate text extraction from text-based PDFs using `pdfplumber`.
    -   Automatically falls back to high-resolution image analysis (OCR) for scanned or image-based PDFs.
-   **Side-by-Side Summary**: Displays the essential extracted content from both documents in a clean, professional, side-by-side view.
-   **Clear Results**: Provides a clear "Approved" or "Needs Review" status and a summary of any found discrepancies.

## Prerequisites

-   Python 3.7+ installed on your system.
-   A Google Gemini API Key.

## Installation

Follow these steps to set up the project on your local machine.

1.  **Clone the Repository**
    (Or simply ensure all the project files are in a single directory).

2.  **Create and Activate a Virtual Environment**
    It is highly recommended to use a virtual environment to manage project dependencies.

    ```bash
    # Create the virtual environment
    python -m venv venv
    ```

    ```bash
    # Activate on Windows
    .\venv\Scripts\activate
    ```

    ```bash
    # Activate on macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Required Packages**
    Install all necessary Python libraries from the `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variable**
    The application requires your Google Gemini API key to function.

    -   Create a new file named `.env` in the root of your project directory.
    -   Open the `.env` file and add the following line, replacing `"YOUR_API_KEY_HERE"` with your actual key:
        ```
        GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```

## How to Run the Code

1.  Ensure your virtual environment is activated.
2.  Run the main application script from your terminal:
    ```bash
    streamlit run app.py
    ```
3.  The app opens and we can give the input files

## Technologies Used

-   **Backend**: Python
-   **Web UI**: streamlit
-   **PDF Text Extraction**: `pdfplumber`
-   **PDF Image Conversion**: `PyMuPDF`
-   **AI & Data Extraction**: Google Gemini Pro
-   **Image Handling**: Pillow
