#!/usr/bin/env python3
"""
Flask Web Application for Global Word Document Find and Replace
Provides a web interface for finding and replacing text across Word documents
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
import logging
from advanced_word_processor import AdvancedWordProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Initialize the word processor
word_processor = AdvancedWordProcessor()

@app.route('/')
def index():
    """Main page with the find and replace interface"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_documents():
    """API endpoint to search for text in documents"""
    try:
        data = request.get_json()
        directory = data.get('directory', '')
        search_term = data.get('search_term', '')
        context_chars = int(data.get('context_chars', 150))
        
        if not directory or not search_term:
            return jsonify({
                'success': False,
                'error': 'Directory and search term are required'
            }), 400
        
        # Validate directory exists
        if not Path(directory).exists():
            return jsonify({
                'success': False,
                'error': f'Directory {directory} does not exist'
            }), 400
        
        # Perform the search
        results = word_processor.scan_directory_advanced(directory, search_term, context_chars)
        
        if results['success']:
            # Add unique IDs to each occurrence for tracking
            for i, occurrence in enumerate(results['occurrences']):
                occurrence['id'] = f"occ_{i}_{hash(occurrence['file_path'] + str(occurrence['start_pos']))}"
                occurrence['replacement_text'] = occurrence['match_text']  # Initialize with original text
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in search_documents: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/replace', methods=['POST'])
def replace_text():
    """API endpoint to replace text in a specific occurrence"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        old_text = data.get('old_text')
        new_text = data.get('new_text')
        occurrence_id = data.get('occurrence_id')
        
        if not all([file_path, old_text, new_text]):
            return jsonify({
                'success': False,
                'error': 'file_path, old_text, and new_text are required'
            }), 400
        
        # Perform the replacement
        result = word_processor.replace_text_advanced(file_path, old_text, new_text, occurrence_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in replace_text: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/replace_all', methods=['POST'])
def replace_all():
    """API endpoint to replace all occurrences of text"""
    try:
        data = request.get_json()
        occurrences = data.get('occurrences', [])
        
        if not occurrences:
            return jsonify({
                'success': False,
                'error': 'No occurrences provided'
            }), 400
        
        results = []
        successful_replacements = 0
        
        for occurrence in occurrences:
            file_path = occurrence.get('file_path')
            old_text = occurrence.get('match_text')
            new_text = occurrence.get('replacement_text')
            
            if file_path and old_text and new_text:
                result = word_processor.replace_text_advanced(file_path, old_text, new_text)
                results.append({
                    'occurrence_id': occurrence.get('id'),
                    'result': result
                })
                
                if result['success']:
                    successful_replacements += 1
        
        return jsonify({
            'success': True,
            'total_processed': len(occurrences),
            'successful_replacements': successful_replacements,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in replace_all: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate_directory', methods=['POST'])
def validate_directory():
    """API endpoint to validate if a directory exists and contains Word files"""
    try:
        data = request.get_json()
        directory = data.get('directory', '')
        
        if not directory:
            return jsonify({
                'valid': False,
                'error': 'Directory path is required'
            })
        
        directory_path = Path(directory)
        
        if not directory_path.exists():
            return jsonify({
                'valid': False,
                'error': f'Directory {directory} does not exist'
            })
        
        if not directory_path.is_dir():
            return jsonify({
                'valid': False,
                'error': f'{directory} is not a directory'
            })
        
        # Count Word files
        word_files = []
        for ext in word_processor.supported_extensions:
            word_files.extend(directory_path.rglob(f"*{ext}"))
        
        return jsonify({
            'valid': True,
            'word_files_count': len(word_files),
            'word_files': [str(f) for f in word_files[:10]]  # Return first 10 files
        })
        
    except Exception as e:
        logger.error(f"Error in validate_directory: {e}")
        return jsonify({
            'valid': False,
            'error': str(e)
        })

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)



