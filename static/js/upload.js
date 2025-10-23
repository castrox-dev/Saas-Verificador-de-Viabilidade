// Upload Drag and Drop Functionality
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('id_file');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const fileRemove = document.getElementById('file-remove');
    const uploadProgress = document.getElementById('upload-progress');
    const progressBar = document.getElementById('progress-bar');
    const submitBtn = document.getElementById('submit-btn');
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);
    
    // Handle file input change
    fileInput.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    });
    
    // Handle click on upload area
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Handle file remove
    if (fileRemove) {
        fileRemove.addEventListener('click', function(e) {
            e.stopPropagation();
            removeFile();
        });
    }
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        uploadArea.classList.add('dragover');
    }
    
    function unhighlight(e) {
        uploadArea.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            
            // Validate file type
            const allowedTypes = [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
                'application/vnd.ms-excel', // .xls
                'text/csv', // .csv
                'application/vnd.google-earth.kml+xml', // .kml
                'application/vnd.google-earth.kmz', // .kmz
                'text/xml', // .kml (alternativo)
                'application/xml', // .kml (alternativo)
                'application/zip' // .kmz (é um arquivo ZIP)
            ];
            
            const allowedExtensions = ['.xlsx', '.xls', '.csv', '.kml', '.kmz'];
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            
            if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
                showError('Tipo de arquivo não suportado. Por favor, envie arquivos nos formatos: .xlsx, .xls, .csv, .kml, .kmz');
                return;
            }
            
            // Validate file size (10MB max)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                showError(`Arquivo muito grande (${sizeMB}MB). Tamanho máximo permitido: 10MB`);
                return;
            }
            
            // Set file to input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            
            // Show file info
            showFileInfo(file);
            
            // Clear any previous errors
            clearErrors();
        }
    }
    
    function showFileInfo(file) {
        if (fileName && fileSize && fileInfo) {
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileInfo.classList.add('show');
            
            // Enable submit button
            if (submitBtn) {
                submitBtn.disabled = false;
            }
        }
    }
    
    function removeFile() {
        // Clear file input
        fileInput.value = '';
        
        // Hide file info
        if (fileInfo) {
            fileInfo.classList.remove('show');
        }
        
        // Hide progress
        if (uploadProgress) {
            uploadProgress.classList.remove('show');
        }
        
        // Disable submit button
        if (submitBtn) {
            submitBtn.disabled = true;
        }
        
        // Clear errors
        clearErrors();
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function showError(message) {
        // Remove existing error messages
        clearErrors();
        
        // Create error element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-danger';
        errorDiv.textContent = message;
        
        // Insert after upload area
        uploadArea.parentNode.insertBefore(errorDiv, uploadArea.nextSibling);
    }
    
    function clearErrors() {
        // Remove all error messages
        const errors = document.querySelectorAll('.text-danger');
        errors.forEach(error => {
            if (error.parentNode === uploadArea.parentNode) {
                error.remove();
            }
        });
    }
    
    // Handle form submission with progress
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (fileInput.files.length > 0) {
                // Show progress bar
                if (uploadProgress) {
                    uploadProgress.classList.add('show');
                    
                    // Simulate progress (since we can't track real upload progress easily)
                    let progress = 0;
                    const interval = setInterval(() => {
                        progress += Math.random() * 15;
                        if (progress > 90) {
                            progress = 90;
                            clearInterval(interval);
                        }
                        if (progressBar) {
                            progressBar.style.width = progress + '%';
                        }
                    }, 200);
                }
                
                // Disable submit button
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
                }
            }
        });
    }
    
    // Initialize state
    if (fileInput.files.length === 0 && submitBtn) {
        submitBtn.disabled = true;
    }
});