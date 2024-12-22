from flask import Flask, request, jsonify, render_template
import pdfplumber
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import torch
import os

app = Flask(__name__)

def download_nltk_resources():
    try:
        nltk.download('stopwords')
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('all')
    except Exception as e:
        print(f"Error downloading NLTK resources: {e}")

download_nltk_resources()

# Load the GPT-2 model and tokenizer
gpt2_model = GPT2LMHeadModel.from_pretrained("gpt2")
gpt2_tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# Set of English stopwords
stop_words = set(stopwords.words('english'))

def extract_text_from_pdf(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + '\n'
    return text.strip()

def process_text(text):
    words = word_tokenize(text)
    filtered_words = [word for word in words if word.isalnum() and word.lower() not in stop_words]
    return filtered_words

def segregate_text(text):
    sections = {
        'Skills': '',
        'Projects': '',
        'Education': '',
        'Experience': '',
        'Certifications': ''
    }

    current_section = None
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if 'skills' in line.lower():
            current_section = 'Skills'
        elif 'projects' in line.lower():
            current_section = 'Projects'
        elif 'education' in line.lower():
            current_section = 'Education'
        elif 'experience' in line.lower():
            current_section = 'Experience'
        elif 'certification' in line.lower():
            current_section = 'Certifications'
        if current_section:
            sections[current_section] += line + ' '

    for key in sections:
        sections[key] = sections[key].strip()
    
    return sections

def get_ai_suggestions(text):
    print("Requesting AI suggestions...")
    try:
        inputs = gpt2_tokenizer.encode(text, return_tensors="pt")
        attention_mask = torch.ones_like(inputs)  # Create an attention mask of ones
        
        outputs = gpt2_model.generate(
            inputs,
            attention_mask=attention_mask,
            max_length=200,
            num_return_sequences=1,
            pad_token_id=gpt2_tokenizer.eos_token_id  # Set pad token ID to eos token ID
        )
        
        suggestions = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
        print("AI response received:", suggestions)
        return suggestions
    except Exception as e:
        print(f"Error getting AI suggestions: {e}")
        return f"Error: Unable to get suggestions. Exception: {e}"

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.pdf'):
        pdf_path = f'temp_{file.filename}'
        file.save(pdf_path)

        try:
            print("Extracting text from PDF...")
            extracted_text = extract_text_from_pdf(pdf_path)
            processed_text = process_text(extracted_text)
            sections = segregate_text(extracted_text)
            print("Text extraction and processing completed.")
            print("Sections:", sections)

            suggestions = get_ai_suggestions(extracted_text)
            return jsonify({'full_text': extracted_text, 'sections': sections, 'suggestions': suggestions})

        except Exception as e:
            print(f"Error processing file: {e}")
            return jsonify({'error': str(e)}), 500

        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    return jsonify({'error': 'Invalid file format'}), 400

if __name__ == '__main__':
    print("Starting the application...")
    app.run(debug=True)