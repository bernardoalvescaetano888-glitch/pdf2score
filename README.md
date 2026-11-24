# Pdf2Score

Aplicativo desktop (Tkinter) que converte partituras em PDF para **MusicXML** ( abre no MuseScore ) e para **MP3**, usando [Audiveris](https://audiveris.github.io/audiveris/) e [MuseScore](https://musescore.org/).

![fluxo](https://img.shields.io/badge/PDF-%3E%20MusicXML%20-%3E%20MP3-blue)

## Recursos

- Seleção de PDF e da **pasta onde salvar** os arquivos gerados.
- Saída configurável: manter `.mxl`, gerar `.mp3` e/ou abrir no MuseScore ao concluir.
- **Histórico** persistente das conversões (últimos 100 registros), com abertura rápida de PDF, MusicXML e MP3.
- **4 temas**: Escuro, Claro, Azul e Verde (salvos automaticamente).
- Log completo da conversão e barra de progresso.
- **Instalação direta do Audiveris**: se não houver versão instalada, o botão *Instalar Audiveris agora* baixa a última release do GitHub e a configura automaticamente.
- Configurações e histórico em `%APPDATA%\Pdf2Score` (Windows) ou `~/.pdf2score`.

## Pré-requisitos

- **Python 3.10+** (apenas para rodar do código-fonte; o `.exe` não precisa).
- **Java 17+** — necessário para o Audiveris.
- **Audiveris 5.x** — detectado automaticamente no PATH ou instalado pelo app.
- **MuseScore 4** — necessário apenas para gerar MP3 e abrir a partitura.

Não há dependências Python externas: `tkinter`, `json`, `subprocess` e `threading` são da biblioteca padrão.

## Uso rápido (código-fonte)

```bat
python main.py
```

1. Aba **Converter**: escolha o PDF e a pasta de destino.
2. Marque *Manter MusicXML* e/ou *Gerar MP3*.
3. Clique em **Converter**.
4. Acompanhe o log. O resultado aparece na aba **Histórico**.

## Gerar o executável

```bat
pip install pyinstaller
python build_exe.py
```

O arquivo fica em `dist\Pdf2Score.exe`.

## Como funciona

```
PDF --Audiveris (-batch -transcribe -export)--> .mxl --MuseScore (-o saida.mp3)--> .mp3
```

O Audiveris faz **OMR** (reconhecimento de partituras), não OCR de texto. O Tesseract embutido dele só lê letras e palavras da partitura.

## Limitações

- OMR não é perfeito: partituras complexas, manuscritos e scans de baixa qualidade podem sair com erros. Revise no MuseScore antes de usar o MP3.
- Use PDFs com notação vetorial ou scans de 300 dpi para melhores resultados.
- Respeite os direitos autorais das partituras que você transcreve.

## Licenças

Audiveris (AGPL), MuseScore (GPL) e SoundFonts têm suas próprias licenças. Este projeto é apenas um automatizador e não inclui binaries de terceiros.
