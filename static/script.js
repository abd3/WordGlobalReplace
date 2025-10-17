/**
 * JavaScript for Global Word Document Find & Replace Application
 * Handles all client-side interactions and API calls
 */

class WordFindReplace {
    constructor() {
        this.currentResults = [];
        this.caseSensitiveCheckbox = document.getElementById('case-sensitive');
        this.lastSearchCaseSensitive = false;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Search form events
        document.getElementById('search-btn').addEventListener('click', () => this.performSearch());
        document.getElementById('validate-dir-btn').addEventListener('click', () => this.validateDirectory());
        const browseBtn = document.getElementById('browse-directory-btn');
        if (browseBtn) {
            browseBtn.addEventListener('click', () => this.openDirectoryPicker());
        }
        
        // Results table events
        document.getElementById('select-all-btn').addEventListener('click', () => this.selectAll());
        document.getElementById('replace-all-btn').addEventListener('click', () => this.replaceAll());
        document.getElementById('select-all-checkbox').addEventListener('change', (e) => this.toggleSelectAll(e.target.checked));
        
        // Enter key support
        document.getElementById('directory').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.validateDirectory();
        });
        document.getElementById('search-term').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performSearch();
        });

        // Global replace term should propagate to each row's replacement input
        const globalReplaceInput = document.getElementById('replace-term');
        globalReplaceInput.addEventListener('input', () => this.updateRowReplacementValues(globalReplaceInput.value));
    }

    async openDirectoryPicker() {
        try {
            const response = await fetch('/api/select_directory', {
                method: 'POST'
            });
            const result = await response.json();

            if (response.ok && result.success) {
                const directoryInput = document.getElementById('directory');
                directoryInput.value = result.directory;
                this.showStatus(`Selected directory: ${result.directory}`, 'success');
                await this.validateDirectory();
            } else if (response.status === 503) {
                this.disableBrowseButton('Folder picker unavailable; enter the path manually.');
                this.showStatus('Folder picker is not available on this system. Enter the path manually.', 'warning');
            } else if (result.error === 'Directory selection canceled') {
                this.showStatus('Directory selection canceled', 'warning');
            } else {
                this.showStatus(result.error || 'Unable to select directory', 'error');
            }
        } catch (error) {
            this.showStatus('Error opening directory picker', 'error');
            this.disableBrowseButton('Folder picker unavailable; enter the path manually.');
        }
    }

    disableBrowseButton(message) {
        const browseBtn = document.getElementById('browse-directory-btn');
        if (browseBtn) {
            browseBtn.disabled = true;
            browseBtn.title = message;
        }
    }

    async validateDirectory() {
        const directory = document.getElementById('directory').value.trim();
        const statusDiv = document.getElementById('directory-status');
        
        if (!directory) {
            this.showStatus('Please enter a directory path', 'error');
            return;
        }

        try {
            const response = await fetch('/api/validate_directory', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ directory })
            });

            const result = await response.json();
            
            if (result.valid) {
                statusDiv.innerHTML = `<i class="fas fa-check-circle"></i> Valid directory with ${result.word_files_count} Word files`;
                statusDiv.className = 'status-message success';
                this.showStatus(`Directory validated: ${result.word_files_count} Word files found`, 'success');
            } else {
                statusDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${result.error}`;
                statusDiv.className = 'status-message error';
                this.showStatus(result.error, 'error');
            }
        } catch (error) {
            statusDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> Error validating directory`;
            statusDiv.className = 'status-message error';
            this.showStatus('Error validating directory', 'error');
        }
    }

    async performSearch() {
        const directory = document.getElementById('directory').value.trim();
        const searchTerm = document.getElementById('search-term').value.trim();
        const contextChars = parseInt(document.getElementById('context-chars').value);
        const caseSensitive = this.caseSensitiveCheckbox?.checked || false;
        
        if (!directory || !searchTerm) {
            this.showStatus('Please enter both directory and search term', 'error');
            return;
        }

        this.showLoading(true);
        this.hideSearchResults();

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    directory,
                    search_term: searchTerm,
                    context_chars: contextChars,
                    case_sensitive: caseSensitive
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.lastSearchCaseSensitive = Boolean(
                    result.case_sensitive !== undefined ? result.case_sensitive : caseSensitive
                );
                this.currentResults = result.occurrences;
                this.displaySearchResults(result);
                this.showStatus(`Found ${result.total_occurrences} occurrences in ${result.files_with_matches} files`, 'success');
            } else {
                this.showStatus(`Search failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showStatus('Error performing search', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displaySearchResults(result) {
        const resultsDiv = document.getElementById('search-results');
        const tbody = document.getElementById('results-tbody');
        const resultsCount = document.getElementById('results-count');
        const filesCount = document.getElementById('files-count');
        
        // Update summary
        resultsCount.textContent = `${result.total_occurrences} occurrences found`;
        filesCount.textContent = `in ${result.files_with_matches} files`;
        
        // Clear previous results
        tbody.innerHTML = '';
        
        // Populate results table
        result.occurrences.forEach((occurrence, index) => {
            const row = this.createResultRow(occurrence, index);
            tbody.appendChild(row);
        });
        
        // Show results
        resultsDiv.style.display = 'block';

        // After rendering rows, initialize replacement inputs from global Replace field if provided
        const globalReplace = document.getElementById('replace-term').value.trim();
        if (globalReplace) {
            this.updateRowReplacementValues(globalReplace);
        }
    }

    createResultRow(occurrence, index) {
        const row = document.createElement('tr');
        row.dataset.occurrenceId = occurrence.id;
        
        const fileName = occurrence.file_path.split('/').pop();
        const contextBefore = occurrence.context_before || '';
        const contextAfter = occurrence.context_after || '';
        const highlightedContext = this.renderHighlightedContext(
            contextBefore,
            occurrence.match_text,
            contextAfter,
            'highlight-original'
        );
        const displayFileName = this.escapeHtml(fileName);
        const displayFilePath = this.escapeHtml(occurrence.file_path);
        
        const globalReplace = document.getElementById('replace-term').value.trim();
        const initialReplacement = globalReplace || occurrence.match_text;

        row.innerHTML = `
            <td>
                <input type="checkbox" class="occurrence-checkbox" data-index="${index}">
            </td>
            <td class="file-name" title="${displayFilePath}">
                <button type="button" class="file-open-link" data-file-path="${displayFilePath}">
                    ${displayFileName}
                </button>
            </td>
            <td class="context-cell">
                <div class="context-text">${highlightedContext}</div>
            </td>
            <td class="replacement-cell">
                <input type="text" class="replacement-input" 
                       value="${initialReplacement}" 
                       data-original="${occurrence.match_text}">
            </td>
            <td>
                <button class="btn btn-sm btn-primary replace-single-btn" 
                        data-index="${index}">
                    <i class="fas fa-exchange-alt"></i> Replace
                </button>
            </td>
        `;
        
        // Add event listeners
        const replaceBtn = row.querySelector('.replace-single-btn');
        replaceBtn.addEventListener('click', () => this.replaceSingle(index));

        const fileLink = row.querySelector('.file-open-link');
        if (fileLink) {
            fileLink.addEventListener('click', (event) => {
                event.preventDefault();
                const path = occurrence.file_path;
                this.openFile(path);
            });
        }
        
        const checkbox = row.querySelector('.occurrence-checkbox');
        checkbox.addEventListener('change', () => this.updateSelectAllState());
        
        row.dataset.contextBefore = contextBefore;
        row.dataset.contextAfter = contextAfter;
        row.dataset.matchText = occurrence.match_text || '';
        
        return row;
    }

    renderHighlightedContext(contextBefore, matchText, contextAfter, highlightClass = 'highlight-original') {
        const before = this.escapeHtml(contextBefore || '');
        const match = this.escapeHtml(matchText || '');
        const after = this.escapeHtml(contextAfter || '');
        return `${before}<mark class="highlight ${highlightClass}">${match}</mark>${after}`;
    }
        if (!filePath) {
            this.showStatus('Missing file path to open', 'error');
            return;
        }

        try {
            const response = await fetch('/api/open_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ file_path: filePath })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                const parts = filePath.split(/[/\\]/);
                const name = parts[parts.length - 1] || filePath;
                this.showStatus(`Opening ${name}...`, 'info');
            } else {
                const error = result && result.error ? result.error : 'Unable to open file';
                this.showStatus(error, 'error');
            }
        } catch (error) {
            this.showStatus('Error launching file', 'error');
        }
    }

    escapeHtml(value) {
        if (value === undefined || value === null) {
            return '';
        }
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    async replaceSingle(index) {
        const occurrence = this.currentResults[index];
        const row = document.querySelector(`tr[data-occurrence-id="${occurrence.id}"]`);
        const replacementInput = row.querySelector('.replacement-input');
        const newText = replacementInput.value.trim();
        
        if (!newText) {
            this.showStatus('Please enter replacement text', 'error');
            return;
        }
        
        if (newText === occurrence.match_text) {
            this.showStatus('Replacement text is the same as original', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/replace', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_path: occurrence.file_path,
                    old_text: occurrence.match_text,
                    new_text: newText,
                    occurrence_id: occurrence.id
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showStatus(`Successfully replaced text in ${occurrence.file_path.split('/').pop()}`, 'success');
                this.applyReplacementToRow(row, occurrence, newText);
                this.updateSelectAllState();
            } else {
                this.showStatus(`Replacement failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showStatus('Error performing replacement', 'error');
        }
    }

    async replaceAll() {
        const selectedOccurrences = this.getSelectedOccurrences();
        
        if (selectedOccurrences.length === 0) {
            this.showStatus('Please select at least one occurrence to replace', 'warning');
            return;
        }
        
        // Prepare replacements with updated text
        const replacements = selectedOccurrences.map(index => {
            const occurrence = this.currentResults[index];
            const row = document.querySelector(`tr[data-occurrence-id="${occurrence.id}"]`);
            const replacementInput = row.querySelector('.replacement-input');
            
            return {
                ...occurrence,
                replacement_text: replacementInput.value.trim()
            };
        });
        
        // Filter out unchanged replacements
        const changedReplacements = replacements.filter(rep => 
            rep.replacement_text !== rep.match_text && rep.replacement_text.trim() !== ''
        );
        
        if (changedReplacements.length === 0) {
            this.showStatus('No changes to apply', 'warning');
            return;
        }
        
        if (!confirm(`Are you sure you want to replace ${changedReplacements.length} occurrences? This action cannot be undone.`)) {
            return;
        }
        
        try {
            const response = await fetch('/api/replace_all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    occurrences: changedReplacements
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showStatus(`Successfully replaced ${result.successful_replacements} out of ${result.total_processed} occurrences`, 'success');
                changedReplacements.forEach(rep => {
                    const row = document.querySelector(`tr[data-occurrence-id="${rep.id}"]`);
                    if (!row) {
                        return;
                    }
                    const original = this.currentResults.find(occ => occ.id === rep.id);
                    this.applyReplacementToRow(row, original, rep.replacement_text);
                });
                this.updateSelectAllState();
            } else {
                this.showStatus(`Bulk replacement failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showStatus('Error performing bulk replacement', 'error');
        }
    }

    applyReplacementToRow(row, occurrence, newText) {
        if (!row) {
            return;
        }

        const contextBefore = row.dataset.contextBefore || (occurrence && occurrence.context_before) || '';
        const contextAfter = row.dataset.contextAfter || (occurrence && occurrence.context_after) || '';
        row.dataset.matchText = newText;

        if (occurrence) {
            occurrence.context_before = contextBefore;
            occurrence.context_after = contextAfter;
            occurrence.full_context = `${contextBefore}${newText}${contextAfter}`;
            occurrence.match_text = newText;
            occurrence.replacement_text = newText;
        }

        const contextDiv = row.querySelector('.context-text');
        if (contextDiv) {
            contextDiv.innerHTML = this.renderHighlightedContext(contextBefore, newText, contextAfter, 'highlight-replaced');
        }

        const replacementInput = row.querySelector('.replacement-input');
        if (replacementInput) {
            replacementInput.value = newText;
        }

        const checkbox = row.querySelector('.occurrence-checkbox');
        if (checkbox) {
            checkbox.checked = false;
        }

        row.classList.add('row-replaced');
    }

    getSelectedOccurrences() {
        const checkboxes = document.querySelectorAll('.occurrence-checkbox:checked');
        return Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
    }

    selectAll() {
        const checkboxes = document.querySelectorAll('.occurrence-checkbox');
        checkboxes.forEach(cb => cb.checked = true);
        document.getElementById('select-all-checkbox').checked = true;
    }

    toggleSelectAll(checked) {
        const checkboxes = document.querySelectorAll('.occurrence-checkbox');
        checkboxes.forEach(cb => cb.checked = checked);
    }

    updateSelectAllState() {
        const checkboxes = document.querySelectorAll('.occurrence-checkbox');
        const checkedBoxes = document.querySelectorAll('.occurrence-checkbox:checked');
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        
        selectAllCheckbox.checked = checkboxes.length > 0 && checkedBoxes.length === checkboxes.length;
        selectAllCheckbox.indeterminate = checkedBoxes.length > 0 && checkedBoxes.length < checkboxes.length;
    }

    updateResultsCount() {
        const remainingRows = document.querySelectorAll('#results-tbody tr').length;
        document.getElementById('results-count').textContent = `${remainingRows} occurrences found`;
        
        if (remainingRows === 0) {
            document.getElementById('search-results').style.display = 'none';
        }
    }

    updateRowReplacementValues(value) {
        const inputs = document.querySelectorAll('.replacement-input');
        inputs.forEach(input => {
            input.value = value;
        });
    }

    showLoading(show) {
        document.getElementById('loading').style.display = show ? 'block' : 'none';
    }

    hideSearchResults() {
        document.getElementById('search-results').style.display = 'none';
    }

    showStatus(message, type = 'info') {
        const statusDiv = document.getElementById('status-messages');
        const statusClass = `toast-${type}`;
        
        const statusElement = document.createElement('div');
        statusElement.className = `toast ${statusClass}`;
        statusElement.setAttribute('role', 'alert');
        statusElement.innerHTML = `
            <span class="toast-icon"><i class="fas fa-${this.getStatusIcon(type)}"></i></span>
            <div class="toast-message">${message}</div>
        `;
        
        statusDiv.appendChild(statusElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (statusElement.parentNode) {
                statusElement.parentNode.removeChild(statusElement);
            }
        }, 5000);
    }

    getStatusIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new WordFindReplace();
});
