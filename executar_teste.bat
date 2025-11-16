@echo off
echo ========================================
echo EFC 02 - Protocolos de Transporte Confiavel
echo ========================================
echo.

REM Verificar se Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale o Python 3.8 ou superior:
    echo 1. Acesse: https://www.python.org/downloads/
    echo 2. Baixe e instale o Python
    echo 3. Certifique-se de marcar "Add Python to PATH" durante a instalacao
    echo.
    pause
    exit /b 1
)

echo Python encontrado!
python --version
echo.

REM Menu de opcoes
echo Escolha qual teste executar:
echo.
echo 1. Fase 1 - RDT (2.0, 2.1, 3.0)
echo 2. Fase 2 - GBN e SR
echo 3. Fase 3 - TCP
echo 4. Todos os testes
echo 5. Sair
echo.
set /p opcao="Digite o numero da opcao: "

if "%opcao%"=="1" (
    echo.
    echo Executando testes da Fase 1...
    python -m unittest discover -s testes -p "test_fase1.py" -v
) else if "%opcao%"=="2" (
    echo.
    echo Executando testes da Fase 2...
    python -m unittest discover -s testes -p "test_fase2.py" -v
) else if "%opcao%"=="3" (
    echo.
    echo Executando testes da Fase 3...
    python -m unittest discover -s testes -p "test_fase3.py" -v
) else if "%opcao%"=="4" (
    echo.
    echo Executando todos os testes...
    echo.
    echo === Fase 1 ===
    python -m unittest discover -s testes -p "test_fase1.py" -v
    echo.
    echo === Fase 2 ===
    python -m unittest discover -s testes -p "test_fase2.py" -v
    echo.
    echo === Fase 3 ===
    python -m unittest discover -s testes -p "test_fase3.py" -v
) else if "%opcao%"=="5" (
    exit /b 0
) else (
    echo Opcao invalida!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Testes concluidos!
echo ========================================
pause


