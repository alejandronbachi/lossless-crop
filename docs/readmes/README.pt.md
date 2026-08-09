<p align="center">
  <img src="../../assets/screenshots/banner.png" width="100%" alt="Lossless Crop">
</p>
<p align="center">
<img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
<img src="https://img.shields.io/badge/Windows-Supported-blue?logo=windows" alt="WindowsSupport">
<img src="https://img.shields.io/badge/macOS-Supported-lighgrey?logo=apple" alt="macOSSupport">
<img src="https://img.shields.io/badge/Linux-Supported-orange?logo=linux" alt="LinuxSupport">
</p>


**Uma aplicação multiplataforma de corte de imagens sem perdas (lossless) com diversos recursos e opções de configuração.**

## Caso de uso
Útil para cortar rapidamente várias imagens em um diretório, uma após a outra.

## Recursos

- Fluxo de trabalho de corte rápido
- Pré-visualização de zoom flutuante configurável
- Suporte a corte **sem perdas (lossless)** para os formatos de imagem *JPEG*, *PNG* e *BMP*
- Suporte a corte **com perdas (lossy)** para os formatos *JPEG* e *WebP*
- Conservação de dados Exif e perfis ICC
- Aplicação, conservação e redimensionamento da proporção (aspect ratio) da área de corte
- Multiplataforma: compatível com **Windows**, **Linux** e **macOS**
- Temas Escuro e Claro
- Atalhos globais de teclado
- Entrada manual da área de corte
- Suporte a arrastar e soltar (drag and drop)
- Menu de diretórios recentes
- Interface de usuário configurável
- Persistência opcional de configurações

## Demonstração
<p align="center">
  <img src="../../assets/screenshots/demo.webp" width="850" alt="Demonstração">
</p>

## Formatos Suportados
- **JPEG**: Modos de corte sem perdas (lossless) ou com perdas (lossy)
- **PNG**: Sem perdas (lossless)
- **BMP**: Sem perdas (lossless)
- **WebP**: Com perdas (lossy)

## Instalação

### Opção 1: Binários
Baixe o binário apropriado na [Página de Lançamentos (Releases)](https://github.com/alejandronbachi/lossless-crop/releases):
- **Windows** (`LosslessCrop-Windows.exe`)
- **Linux** (`LosslessCrop-Linux`)
- **macOS** (`LosslessCrop-macOS.tar.gz`)

[![GitHubRelease](https://img.shields.io/github/v/release/alejandronbachi/lossless-crop?color=blue)](https://github.com/alejandronbachi/lossless-crop/releases)

## Início Rápido / Guia de Uso
1. Abra um diretório com imagens 
2. Desenhe a seleção sobre a imagem
3. Pressione `space` para cortar e avançar para a próxima imagem

## Manual do Usuário
Por favor, leia o [Manual do Usuário](/docs/user_manual_pt.md) para mais instruções, especialmente se precisar saber como o corte sem perdas funciona, caso contrário, o ajuste (snapping) da área de seleção pode ser um comportamento inesperado.

## Atalhos Globais de Teclado e Controles do Mouse

| Ações de Teclado | Teclas | Ações do Mouse | Controles |
| :--- | :--- | :--- | :--- |
| **Cortar e Próximo** | <kbd>Space</kbd> | **Desenhar Caixa** | <kbd>Clique Esquerdo</kbd> + Arrastar |
| **Cortar** | <kbd>S</kbd> ou <kbd>Middle-Click</kbd> | **Mover Caixa** | <kbd>Clique Direito</kbd> + Arrastar |
| **Abrir Diretório** | <kbd>O</kbd> | **Navegar** | <kbd>Roda do Mouse</kbd> |
| **Abrir Imagem** | <kbd>I</kbd> | **Cortar** | <kbd>Clique do Meio</kbd> |
| **Avançar** | <kbd>F</kbd> ou <kbd>D</kbd> | | |
| **Voltar** | <kbd>B</kbd> ou <kbd>A</kbd> | | |
| **Girar em Horário** | <kbd>R</kbd> | | |
| **Alternar Pré-visualização** | <kbd>P</kbd> ou <kbd>Q</kbd> | | |
| **Alternar Menu** | <kbd>Alt</kbd> | | |
| **Sair do App** | <kbd>Esc</kbd> | | |


## Vitrine: tema claro, comandos, HUD de zoom, options e uma capivara
  <br>
  <p align="center">
    <img src="../../assets/screenshots/showcase_1.webp" alt="Primeira Tela" width="70%">
    <img src="../../assets/screenshots/showcase_2.webp" alt="Segunda Tela" width="20%">
  </p>


## Desenvolvimento e Contribuição
Estarei atualizando a documentação para facilitar a colaboração com o projeto em breve. Me avise se tiver interesse em ajudar.
O projeto foi construído em Python com as bibliotecas PyQt6 e Pillow. Posso testar a migração para PySide6 em breve.
Como estou lançando como FOSS e também na Windows Marketplace na tentativa de obter algum financiamento, os colaboradores precisarão assinar um CLA; automatizarei isso em breve.

Pré-requisitos:
```
PyQt6==6.7.1
Pillow==10.4.0
```

## Roadmap
Dependendo do tempo disponível, uso do aplicativo e solicitações dos usuários.
- Internacionalização
- Redimensionamento sem perdas
- Operações em lote

## Licença
Este projeto está licenciado sob a Licença GNU GPL 3 - consulte o arquivo [`LICENSE`](../../LICENSE) para obter detalhes.
<a href="https://github.com/alejandronbachi/lossless-crop/blob/main/LICENSE"> <img src="https://img.shields.io/github/license/alejandronbachi/lossless-crop?color=green" alt="Licença"></a>


## Apoie Meu Trabalho

Se você achar este projeto útil, pode apoiar o desenvolvimento dele via Binance Pay!

**Meu ID do Binance Pay:** `1228818247`

*Escaneie o código QR abaixo usando seu aplicativo móvel da Binance para doar instantaneamente com 0% de taxas de gás de rede (Suporta USDT, BTC, ETH e BNB).*

<img src="../../assets/screenshots/binance_qr.jpg" width="220" alt="QR Code Binance Pay">
