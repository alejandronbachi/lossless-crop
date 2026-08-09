# Lossless Crop

## Caso de uso
Este aplicativo é útil para recortar rapidamente várias imagens em um diretório, uma após a outra.

## Formatos suportados
- **JPEG**: Modos de recorte sem perdas (Lossless) ou com perdas (Lossy)
- **PNG**: Sem perdas
- **BMP**: Sem perdas
- **WebP**: Com perdas

## Nota sobre o recorte sem perdas
O ajuste à grade é necessário para realizar um recorte sem perdas em uma imagem *JPEG*, pois as imagens JPEG agrupam os pixels em blocos chamados MCU (Minimum Coded Units). Os limites do recorte devem se alinhados com esses blocos para realizar o recorte sem recompressão e sem perda de qualidade.
É por isso que, ao selecionar o motor sem perdas em uma imagem JPEG, a área selecionada se ajustará automaticamente aos blocos MCU mais próximos. Se você não quiser isso, pode usar o motor pixel-perfeito, que é com perdas, mas permite escolher a área de recorte livremente.
O recorte de *PNG* ou *BMP* é sempre sem perdas e não requer ajuste à grade.
O *WebP* neste aplicativo é tratado como recorte com perdas.

## Fluxo de trabalho básico
1. Abra um diretório com imagens
2. Desenhe a seleção sobre a imagem
3. Recorte e vá para a próxima imagem

## Zoom com a pré-visualização flutuante (HUD)
Você pode ativar a pré-visualização flutuante pressionando `P` ou `Q` ou através da gaveta de configurações.
Esta pré-visualização pode ser redimensionada arrastando nas bordas com o botão esquerdo e movida segurando o botão direito, de forma consistente com a área de seleção.
Se `Preview HUD` estiver marcado em 'Layout Memory', o tamanho e a posição do HUD atual serão salvos e restaurados na próxima vez que você abrir o aplicativo.

### Fluxo de trabalho A: "Não gosto do zoom flutuante"
Uma maneira fácil de obter outro zoom é trabalhar com `Overwrite` ativo e pressionar `S` para recortar a área desejada; a cada recorte, a imagem atual mudará e será recarregada mostrando apenas a parte recortada.
Lembre-se de que isso sobrescreve os arquivos de origem.

### Fluxo de trabalho B: "Não gosto do zoom flutuante"
E se você precisar recortar diferentes partes pequenas de uma imagem grande? Você pode desativar `Overwrite`, recortar todas as partes necessárias em todas as imagens desejadas, abrir a subpasta 'cropped' onde essas pequenas partes estarão e recortá-las novamente com mais precisão.

## Opções da barra de ferramentas
### Motor (Engine)
- **Lossless**: Usa o motor jpegtran para realizar o recorte sem perdas de imagens JPEG. Se a imagem não for um *JPEG* válido, esta opção é ignorada.
- **Pixel-Perfect**: Usa o motor Pillow para recortar, com alguma perda menor de qualidade para *JPEG* e *WebP* ou sem perdas para *PNG* e *BMP*.

### Proporção forçada (Forced Ratio)
Esta opção impõe uma proporção de aspecto na caixa de retângulo de recorte. Opções disponíveis:
- Livre (Freeform)
- Proporção original (Source Ratio)
- Quadrado 1:1 (1:1 Square)
- 16:9 Widescreen (16:9 Widescreen)
- 4:3 Standard (4:3 Standard)

### Feedback de ajuste à grade (Snapping Feedback)
Altera como o ajuste à grade é exibido ao usuário.
Isso se aplica apenas ao recorte sem perdas (o motor Lossless deve estar selecionado e a imagem deve ser um JPEG válido).
Há 3 opções:
- **Real Time Snap**: O ajuste é feito em tempo real enquanto o usuário desenha a área de recorte.
- **Post Release Snap**: O ajuste é exibido apenas quando o usuário termina de desenhar.
- **Ghosting**: Outra caixa é desenhada enquanto o usuário desenha, mostrando a grade ajustada.

### Entradas manuais da área de recorte
As caixas de número (spinboxes) podem ser usadas para inserir o tamanho desejado da área de recorte.
*Importante*: Para que os valores sejam registrados, o usuário deve pressionar Enter ou sair dos campos de edição.

### Manter seleção (Keep selection)
Útil para carregar a caixa de seleção de uma imagem para a outra se os tamanhos de recorte forem semelhantes.

### Sobrescrever (Overwrite)
Ativar esta opção sobrescreve o arquivo de origem após o recorte.

### Ícone de configurações (Settings Gear)
Abre a gaveta de configurações.

## Gaveta de configurações
Fornece muitas opções de visibilidade e persistência.
### Configurações gerais
- Salvar configurações (Save settings): persiste as configurações do usuário e as recarrega na próxima utilização.
- Abrir última pasta (Auto-open last folder): abre o último diretório de trabalho utilizado na inicialização.
- Ajustar pré-visualização (Fit preview): altera como a imagem é exibida no HUD de visualização. Ativá-lo mostra a área selecionada completa.
- Tema escuro (Dark Theme): ativa o tema escuro. O tema claro é aplicado caso contrário.

### Exibição (Show / Display)
Afeta o que é mostrado ou ocultado na interface do usuário.

### Memória de layout (Layout Memory)
- Janela principal (Main Window): recarrega o tamanho e a posição da janela principal ao carregar o aplicativo.
- Pré-visualização HUD (Preview HUD): recarrega o tamanho e a posição do HUD de pré-visualização ao carregar o aplicativo.

## Barra de menus
A barra de menus pode ser alternada com *Alt*.
Os comandos regulares são explicados na seção de comandos, apenas as ações especiais são explicadas aqui.

- Arquivo -> Ver Logs: Abre a pasta com os logs do aplicativo para leitura, se necessário.
- Recente -> Diretório: Abre o diretório selecionado da lista recente.
- Ajuda -> Manual do Usuário: Mostra este manual do usuário.
- Ajuda -> Sobre: Exibe a janela Sobre.

## Atalhos de teclado globais e controles do mouse

| Ações do teclado | Teclas | Ações do mouse | Controles |
| :--- | :--- | :--- | :--- |
| **Recortar e Próximo** | <kbd>Espaço</kbd> | **Desenhar Caixa** | <kbd>Clique esquerdo</kbd> + Arrastar |
| **Recortar** | <kbd>S</kbd> ou <kbd>Clique do meio</kbd> | **Mover Caixa** | <kbd>Clique direito</kbd> + Arrastar |
| **Abrir Diretório** | <kbd>O</kbd> | **Navegar** | <kbd>Roda do mouse</kbd> |
| **Abrir Imagem** | <kbd>I</kbd> | **Recortar** | <kbd>Clique do meio</kbd> |
| **Avançar** | <kbd>F</kbd> ou <kbd>D</kbd> | | |
| **Voltar** | <kbd>B</kbd> ou <kbd>A</kbd> | | |
| **Girar (horário)** | <kbd>R</kbd> | | |
| **Alternar Pré-visualização** | <kbd>P</kbd> ou <kbd>Q</kbd> | | |
| **Alternar Menu** | <kbd>Alt</kbd> | | |
| **Sair do App** | <kbd>Esc</kbd> | | |

## Comandos
Existem várias maneiras de executar as mesmas ações no aplicativo, escolha a que melhor lhe convier:
- *Abrir Diretório*: Abre uma pasta com imagens e a carrega no aplicativo. Deve conter imagens válidas.
- *Abrir Imagem*: Permite escolher uma imagem individual para abrir o diretório na imagem específica.
- *Avançar*: Move para a próxima imagem.
- *Voltar*: Move para a imagem anterior.
- *Recortar*: Recorta a área selecionada.
- *Recortar e Próximo*: Recorta e avança para a próxima imagem.
- *Girar*: Gira a imagem no sentido horário.
- *Sair*: Sai do aplicativo.

## Suporte a Arrastar e Soltar (Drag and Drop)
- Arrastar um diretório para o aplicativo é o mesmo que o comando Abrir Diretório.
- Arrastar uma foto para o aplicativo é o mesmo que o comando Abrir Imagem.

## Ícones da barra de ferramentas
À esquerda da barra de ferramentas, os ícones podem ser usados para acionar Abrir Diretório, Abrir Imagem, Recortar, Recortar e Próximo e Girar, nessa ordem de aparição.
