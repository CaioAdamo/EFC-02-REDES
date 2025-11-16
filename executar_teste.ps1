Write-Host "========================================" -ForegroundColor Cyan
Write-Host "EFC 02 - Protocolos de Transporte Confiavel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Python esta instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python encontrado: $pythonVersion" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERRO] Python nao encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, instale o Python 3.8 ou superior:" -ForegroundColor Yellow
    Write-Host "1. Acesse: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "2. Baixe e instale o Python" -ForegroundColor Yellow
    Write-Host "3. Certifique-se de marcar 'Add Python to PATH' durante a instalacao" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Menu de opcoes
Write-Host "Escolha qual teste executar:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Fase 1 - RDT (2.0, 2.1, 3.0)" -ForegroundColor White
Write-Host "2. Fase 2 - GBN e SR" -ForegroundColor White
Write-Host "3. Fase 3 - TCP" -ForegroundColor White
Write-Host "4. Todos os testes" -ForegroundColor White
Write-Host "5. Sair" -ForegroundColor White
Write-Host ""

$opcao = Read-Host "Digite o numero da opcao"

switch ($opcao) {
    "1" {
        Write-Host ""
        Write-Host "Executando testes da Fase 1..." -ForegroundColor Green
        python -m unittest discover -s testes -p "test_fase1.py" -v
    }
    "2" {
        Write-Host ""
        Write-Host "Executando testes da Fase 2..." -ForegroundColor Green
        python -m unittest discover -s testes -p "test_fase2.py" -v
    }
    "3" {
        Write-Host ""
        Write-Host "Executando testes da Fase 3..." -ForegroundColor Green
        python -m unittest discover -s testes -p "test_fase3.py" -v
    }
    "4" {
        Write-Host ""
        Write-Host "Executando todos os testes..." -ForegroundColor Green
        Write-Host ""
        Write-Host "=== Fase 1 ===" -ForegroundColor Cyan
        python -m unittest discover -s testes -p "test_fase1.py" -v
        Write-Host ""
        Write-Host "=== Fase 2 ===" -ForegroundColor Cyan
        python -m unittest discover -s testes -p "test_fase2.py" -v
        Write-Host ""
        Write-Host "=== Fase 3 ===" -ForegroundColor Cyan
        python -m unittest discover -s testes -p "test_fase3.py" -v
    }
    "5" {
        exit 0
    }
    default {
        Write-Host "Opcao invalida!" -ForegroundColor Red
        Read-Host "Pressione Enter para sair"
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testes concluidos!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Pressione Enter para sair"


