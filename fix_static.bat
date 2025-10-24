@echo off
echo ========================================
echo   CORRIGINDO ARQUIVOS ESTATICOS
echo ========================================

echo.
echo Ativando ambiente virtual...
call venv\Scripts\activate

echo.
echo [1/4] Limpando arquivos estaticos coletados...
if exist staticfiles rmdir /s /q staticfiles

echo.
echo [2/4] Coletando arquivos estaticos...
python manage.py collectstatic --noinput

echo.
echo [3/4] Verificando arquivos estaticos...
dir staticfiles\css
dir staticfiles\js
dir staticfiles\img

echo.
echo [4/4] Testando servidor...
echo.
echo Iniciando servidor de teste...
echo Acesse: http://127.0.0.1:8000/static/css/login.css
echo Pressione Ctrl+C para parar o teste
echo.
python manage.py runserver --noreload
