// JavaScript para a tela de administração de mapas

document.addEventListener('DOMContentLoaded', function() {
    initializeAdminFeatures();
});

function initializeAdminFeatures() {
    initializeSearch();
    initializeFilters();
    initializeBulkActions();
    initializeTableSorting();
    initializeDeleteConfirmation();
}

// Funcionalidade de busca em tempo real
function initializeSearch() {
    const searchInput = document.getElementById('searchMaps');
    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const tableRows = document.querySelectorAll('.maps-table tbody tr');

        tableRows.forEach(row => {
            const fileName = row.querySelector('.file-name')?.textContent.toLowerCase() || '';
            const description = row.querySelector('.file-description')?.textContent.toLowerCase() || '';
            const uploader = row.querySelector('.uploader-name')?.textContent.toLowerCase() || '';

            if (fileName.includes(searchTerm) || description.includes(searchTerm) || uploader.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });

        updateResultsCount();
    });
}

// Filtros por status
function initializeFilters() {
    const statusFilter = document.getElementById('statusFilter');
    if (!statusFilter) return;

    statusFilter.addEventListener('change', function() {
        const selectedStatus = this.value;
        const tableRows = document.querySelectorAll('.maps-table tbody tr');

        tableRows.forEach(row => {
            if (selectedStatus === 'all') {
                row.style.display = '';
            } else {
                const statusBadge = row.querySelector('.status-badge');
                const rowStatus = statusBadge?.classList.contains('processed') ? 'processed' : 'pending';
                
                if (rowStatus === selectedStatus) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        });

        updateResultsCount();
    });
}

// Ações em lote
function initializeBulkActions() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    const bulkActionSelect = document.getElementById('bulkAction');
    const applyBulkButton = document.getElementById('applyBulk');

    if (!selectAllCheckbox || !bulkActionSelect || !applyBulkButton) return;

    // Selecionar/deselecionar todos
    selectAllCheckbox.addEventListener('change', function() {
        rowCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateBulkActionButton();
    });

    // Atualizar estado do botão quando checkboxes individuais mudam
    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectAllState();
            updateBulkActionButton();
        });
    });

    // Aplicar ação em lote
    applyBulkButton.addEventListener('click', function() {
        const selectedAction = bulkActionSelect.value;
        const selectedRows = document.querySelectorAll('.row-checkbox:checked');

        if (selectedRows.length === 0) {
            alert('Selecione pelo menos um mapa para aplicar a ação.');
            return;
        }

        if (selectedAction === 'delete') {
            if (confirm(`Tem certeza que deseja excluir ${selectedRows.length} mapa(s) selecionado(s)?`)) {
                // Aqui você implementaria a lógica de exclusão em lote
                console.log('Excluindo mapas:', selectedRows);
            }
        } else if (selectedAction === 'download') {
            // Implementar download em lote
            console.log('Baixando mapas:', selectedRows);
        }
    });
}

function updateSelectAllState() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');

    if (checkedBoxes.length === 0) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = false;
    } else if (checkedBoxes.length === rowCheckboxes.length) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = true;
    } else {
        selectAllCheckbox.indeterminate = true;
    }
}

function updateBulkActionButton() {
    const applyBulkButton = document.getElementById('applyBulk');
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    
    if (applyBulkButton) {
        applyBulkButton.disabled = checkedBoxes.length === 0;
    }
}

// Ordenação da tabela
function initializeTableSorting() {
    const sortableHeaders = document.querySelectorAll('.sortable');
    
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.dataset.column;
            const currentOrder = this.dataset.order || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // Remover indicadores de ordenação de outros cabeçalhos
            sortableHeaders.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
                h.dataset.order = '';
            });
            
            // Adicionar indicador ao cabeçalho atual
            this.classList.add(newOrder === 'asc' ? 'sort-asc' : 'sort-desc');
            this.dataset.order = newOrder;
            
            sortTable(column, newOrder);
        });
    });
}

function sortTable(column, order) {
    const tbody = document.querySelector('.maps-table tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        let aValue, bValue;
        
        switch(column) {
            case 'name':
                aValue = a.querySelector('.file-name')?.textContent || '';
                bValue = b.querySelector('.file-name')?.textContent || '';
                break;
            case 'size':
                aValue = parseFloat(a.querySelector('.file-size')?.textContent.replace(/[^\d.]/g, '') || '0');
                bValue = parseFloat(b.querySelector('.file-size')?.textContent.replace(/[^\d.]/g, '') || '0');
                break;
            case 'date':
                aValue = new Date(a.querySelector('.upload-date')?.textContent || '');
                bValue = new Date(b.querySelector('.upload-date')?.textContent || '');
                break;
            case 'status':
                aValue = a.querySelector('.status-badge')?.textContent || '';
                bValue = b.querySelector('.status-badge')?.textContent || '';
                break;
            default:
                return 0;
        }
        
        if (typeof aValue === 'string') {
            aValue = aValue.toLowerCase();
            bValue = bValue.toLowerCase();
        }
        
        if (order === 'asc') {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });
    
    // Reordenar as linhas na tabela
    rows.forEach(row => tbody.appendChild(row));
}

// Confirmação de exclusão
function initializeDeleteConfirmation() {
    const deleteButtons = document.querySelectorAll('.btn-delete');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const fileName = this.closest('tr').querySelector('.file-name')?.textContent || 'este mapa';
            
            if (confirm(`Tem certeza que deseja excluir o mapa "${fileName}"? Esta ação não pode ser desfeita.`)) {
                // Aqui você redirecionaria para a URL de exclusão
                window.location.href = this.href;
            }
        });
    });
}

// Atualizar contador de resultados
function updateResultsCount() {
    const visibleRows = document.querySelectorAll('.maps-table tbody tr[style=""], .maps-table tbody tr:not([style])');
    const totalRows = document.querySelectorAll('.maps-table tbody tr');
    const resultsCount = document.getElementById('resultsCount');
    
    if (resultsCount) {
        resultsCount.textContent = `Mostrando ${visibleRows.length} de ${totalRows.length} mapas`;
    }
}

// Função para formatar tamanho de arquivo
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Função para animar contadores
function animateCounters() {
    const counters = document.querySelectorAll('.stat-number');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent);
        const increment = target / 50;
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target;
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current);
            }
        }, 20);
    });
}

// Inicializar animações quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(animateCounters, 500);
});

// Função para exportar dados
function exportData(format) {
    const visibleRows = document.querySelectorAll('.maps-table tbody tr[style=""], .maps-table tbody tr:not([style])');
    const data = [];
    
    visibleRows.forEach(row => {
        const rowData = {
            nome: row.querySelector('.file-name')?.textContent || '',
            descricao: row.querySelector('.file-description')?.textContent || '',
            tamanho: row.querySelector('.file-size')?.textContent || '',
            status: row.querySelector('.status-badge')?.textContent || '',
            data_upload: row.querySelector('.upload-date')?.textContent || '',
            enviado_por: row.querySelector('.uploader-name')?.textContent || ''
        };
        data.push(rowData);
    });
    
    if (format === 'csv') {
        exportToCSV(data);
    } else if (format === 'json') {
        exportToJSON(data);
    }
}

function exportToCSV(data) {
    const headers = ['Nome', 'Descrição', 'Tamanho', 'Status', 'Data Upload', 'Enviado Por'];
    const csvContent = [
        headers.join(','),
        ...data.map(row => Object.values(row).map(value => `"${value}"`).join(','))
    ].join('\n');
    
    downloadFile(csvContent, 'mapas_empresa.csv', 'text/csv');
}

function exportToJSON(data) {
    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(jsonContent, 'mapas_empresa.json', 'application/json');
}

function downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
}