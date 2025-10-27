# Exemplo de Estrutura Flask para Integração

## 📁 Estrutura Sugerida

```
verificador_flask/
├── app.py                 # Aplicação principal
├── config.py             # Configurações
├── requirements.txt      # Dependências
├── models/
│   ├── __init__.py
│   ├── analysis.py       # Modelos de análise
│   └── results.py        # Modelos de resultados
├── services/
│   ├── __init__.py
│   ├── verificador.py    # Lógica principal do verificador
│   ├── file_processor.py # Processamento de arquivos
│   └── report_generator.py # Geração de relatórios
├── api/
│   ├── __init__.py
│   ├── routes.py         # Rotas da API
│   └── middleware.py     # Middleware (CORS, auth)
├── utils/
│   ├── __init__.py
│   ├── validators.py     # Validadores
│   └── helpers.py        # Funções auxiliares
└── tests/
    ├── __init__.py
    └── test_verificador.py
```

## 🔧 Exemplo de app.py

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from services.verificador import VerificadorService
from api.routes import api_bp
import logging

app = Flask(__name__)
CORS(app)  # Permitir requisições do Django

# Configurações
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Registrar blueprints
app.register_blueprint(api_bp)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'verificador'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
```

## 🔧 Exemplo de services/verificador.py

```python
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class VerificadorService:
    """Serviço principal do verificador de viabilidade"""
    
    @staticmethod
    def verificar_arquivo(file_path: str, file_type: str, 
                         company_id: int, user_id: int, 
                         options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Verifica viabilidade de um arquivo CTO
        
        Args:
            file_path: Caminho para o arquivo
            file_type: Tipo do arquivo (xlsx, csv, kml, etc.)
            company_id: ID da empresa
            user_id: ID do usuário
            options: Opções adicionais de análise
            
        Returns:
            Dict com resultados da análise
        """
        try:
            # Gerar ID único para a análise
            analysis_id = str(uuid.uuid4())
            
            # Validar arquivo
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Processar arquivo baseado no tipo
            if file_type.lower() in ['xlsx', 'xls']:
                results = VerificadorService._process_excel(file_path)
            elif file_type.lower() == 'csv':
                results = VerificadorService._process_csv(file_path)
            elif file_type.lower() in ['kml', 'kmz']:
                results = VerificadorService._process_kml(file_path)
            else:
                raise ValueError(f"Tipo de arquivo não suportado: {file_type}")
            
            # Calcular score de viabilidade
            viability_score = VerificadorService._calculate_viability_score(results)
            
            # Gerar relatório se solicitado
            report_url = None
            if options and options.get('generate_report'):
                report_url = VerificadorService._generate_report(analysis_id, results)
            
            return {
                'success': True,
                'analysis_id': analysis_id,
                'status': 'completed',
                'results': {
                    'viability_score': viability_score,
                    'issues': results.get('issues', []),
                    'recommendations': results.get('recommendations', []),
                    'report_url': report_url,
                    'processed_at': datetime.now().isoformat()
                },
                'processing_time': results.get('processing_time', 0),
                'file_info': {
                    'name': os.path.basename(file_path),
                    'type': file_type,
                    'size': os.path.getsize(file_path)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'analysis_id': analysis_id if 'analysis_id' in locals() else None,
                'status': 'failed'
            }
    
    @staticmethod
    def _process_excel(file_path: str) -> Dict[str, Any]:
        """Processa arquivo Excel"""
        # Implementar lógica de processamento Excel
        return {
            'issues': [],
            'recommendations': [],
            'processing_time': 5.2
        }
    
    @staticmethod
    def _process_csv(file_path: str) -> Dict[str, Any]:
        """Processa arquivo CSV"""
        # Implementar lógica de processamento CSV
        return {
            'issues': [],
            'recommendations': [],
            'processing_time': 3.1
        }
    
    @staticmethod
    def _process_kml(file_path: str) -> Dict[str, Any]:
        """Processa arquivo KML/KMZ"""
        # Implementar lógica de processamento KML
        return {
            'issues': [],
            'recommendations': [],
            'processing_time': 7.8
        }
    
    @staticmethod
    def _calculate_viability_score(results: Dict[str, Any]) -> int:
        """Calcula score de viabilidade (0-100)"""
        # Implementar algoritmo de cálculo
        base_score = 100
        
        # Deduzir pontos por issues encontradas
        issues_count = len(results.get('issues', []))
        score_deduction = min(issues_count * 5, 50)  # Máximo 50 pontos de dedução
        
        return max(base_score - score_deduction, 0)
    
    @staticmethod
    def _generate_report(analysis_id: str, results: Dict[str, Any]) -> str:
        """Gera relatório PDF"""
        # Implementar geração de relatório
        return f"/reports/{analysis_id}.pdf"
```

## 🔧 Exemplo de api/routes.py

```python
from flask import Blueprint, request, jsonify
from services.verificador import VerificadorService
import logging

api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@api_bp.route('/verificar', methods=['POST'])
def verificar_arquivo():
    """Endpoint para verificação de arquivo"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['file_path', 'file_type', 'company_id', 'user_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório ausente: {field}'
                }), 400
        
        # Executar verificação
        result = VerificadorService.verificar_arquivo(
            file_path=data['file_path'],
            file_type=data['file_type'],
            company_id=data['company_id'],
            user_id=data['user_id'],
            options=data.get('options', {})
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro na verificação: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@api_bp.route('/status/<analysis_id>', methods=['GET'])
def get_analysis_status(analysis_id):
    """Endpoint para verificar status da análise"""
    # Implementar verificação de status
    return jsonify({
        'analysis_id': analysis_id,
        'status': 'completed',
        'progress': 100
    })
```

## 📋 requirements.txt exemplo

```txt
Flask==2.3.3
Flask-CORS==4.0.0
pandas==2.0.3
openpyxl==3.1.2
lxml==4.9.3
requests==2.31.0
python-dotenv==1.0.0
gunicorn==21.2.0
```
