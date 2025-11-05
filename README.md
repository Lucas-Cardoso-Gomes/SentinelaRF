# Analisador de RF Autônomo com HackRF e IA

Este projeto é um programa em Python que transforma um HackRF One em um analisador de radiofrequência (RF) autônomo e inteligente. Ele varre um espectro de frequência definido, identifica o sinal mais forte e utiliza um modelo de linguagem de IA (através do Ollama) para descrever o sinal e otimizar dinamicamente as configurações de recepção.

## Funcionalidades

-   **Varredura Automatizada:** Varre uma faixa de frequência personalizável usando `hackrf_sweep`.
-   **Controle de Sensibilidade:** Gerencia automaticamente os ganhos LNA e VGA do HackRF One.
-   **Análise com IA:** Utiliza o Ollama (com o modelo `gamma:1b`) para:
    -   Gerar uma descrição textual do provável tipo de sinal detectado.
    -   Sugerir novos ajustes de ganho para melhorar a qualidade da recepção.
-   **Registro Detalhado:** Salva todas as descobertas em um arquivo `rf_scan_log.csv`, incluindo timestamp, frequência, configurações de ganho e as análises da IA.
-   **Decodificação (Assistida por IA):** O programa utiliza a análise da IA para sugerir o tipo de modulação do sinal (ex: NFM, AM, FSK) e o registra no log. A função de decodificação serve como um ponto de partida para a integração com ferramentas externas especializadas.

## Como Funciona

O programa opera em um ciclo contínuo:

1.  **Varredura:** Executa `hackrf_sweep` com as configurações de ganho atuais (LNA e VGA) para encontrar a frequência com o sinal mais potente na faixa definida.
2.  **Análise:** Envia os dados do sinal (frequência, potência, largura de banda) para a API do Ollama.
3.  **Descrição:** O Ollama analisa os dados e retorna uma breve descrição do que o sinal provavelmente é (ex: "Comunicação de rádio bidirecional", "Sinal de dados FM").
4.  **Otimização:** O programa pede ao Ollama sugestões para ajustar os ganhos LNA e VGA com base na potência do sinal.
5.  **Registro:** Todas as informações são salvas como uma nova linha no arquivo `rf_scan_log.csv`.
6.  **Ajuste:** O programa atualiza os seus próprios parâmetros de ganho com base nas sugestões da IA.
7.  **Repetição:** O ciclo recomeça, utilizando as novas configurações para a próxima varredura.

## Pré-requisitos

### Hardware
-   Um [HackRF One](https://greatscottgadgets.com/hackrf/)

### Software
-   Python 3.6+
-   `hackrf-tools` (ferramentas de linha de comando do HackRF)
-   Servidor [Ollama](https://ollama.ai/) em execução com o modelo `gamma:1b`

## Instalação

Para instruções detalhadas sobre como instalar as dependências de sistema e configurar o ambiente Python, por favor, consulte o arquivo:
-   **[setup_instructions.md](./setup_instructions.md)**

## Executando a Interface Web

1.  **Certifique-se de que todos os pré-requisitos** (Hardware e Software) estão instalados e configurados corretamente.
2.  **Instale as dependências Python**, incluindo as novas bibliotecas para o servidor web:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Inicie a aplicação:**
    ```bash
    python3 app.py
    ```
4.  **Acesse a interface:** Abra o seu navegador e acesse o endereço [http://localhost:5000](http://localhost:5000).

Você verá o painel do analisador, que começará a exibir logs e sinais detectados em tempo real. O servidor iniciará a varredura de RF automaticamente em segundo plano. Para parar o servidor e a varredura, pressione `Ctrl+C` no terminal onde o `app.py` está sendo executado.

## Configuração

Você pode personalizar o comportamento da varredura editando as constantes no início do arquivo `rf_analyzer.py`:

-   `SCAN_RANGE_MHZ`: Define a faixa de frequência (início e fim) a ser varrida, em MHz.
-   `SCAN_BIN_WIDTH_HZ`: Define a resolução da varredura, em Hz. Valores menores são mais precisos, mas podem gerar mais dados.
-   `SCAN_NUM_SAMPLES`: Controla o tempo gasto em cada segmento de frequência.
    -   **Valores maiores** (ex: `262144`) tornam a varredura mais lenta, mas aumentam a chance de detectar sinais fracos ou intermitentes (como uma transmissão de voz).
    -   **Valores menores** (ex: `65536`) tornam a varredura mais rápida, ideal para encontrar sinais contínuos.

## Formato do Log (`rf_scan_log.csv`)

O arquivo de log é um CSV com as seguintes colunas:

-   **Timestamp:** Data e hora da detecção.
-   **Frequency (MHz):** Frequência central do sinal mais forte encontrado.
-   **Modulation:** Tipo de modulação (atualmente "Unknown").
-   **LNA Gain:** Ganho do amplificador de baixo ruído (LNA) utilizado na varredura.
-   **VGA Gain:** Ganho do amplificador de ganho variável (VGA) utilizado.
-   **AMP Enabled:** Se o amplificador de 20dB estava ativado (`True`/`False`).
-   **Ollama Description:** A descrição do sinal gerada pela IA.
-   **Ollama Suggestions:** As sugestões de ajuste de ganho geradas pela IA.
-   **Decoded Data:** Placeholder para dados decodificados.

## Sobre a Decodificação de Sinais

A decodificação de sinais de rádio é uma tarefa complexa que depende fundamentalmente do **tipo de modulação** e do **protocolo de dados** utilizado. Um decodificador "universal" não é prático. Por exemplo, a decodificação de uma transmissão de rádio FM é completamente diferente da decodificação de um sinal Wi-Fi ou de um sensor de temperatura sem fio.

Este programa aborda este desafio da seguinte forma:

1.  **Identificação de Modulação via IA:** Ele pede ao modelo Ollama para sugerir o tipo de modulação mais provável com base nas características do sinal. Este palpite educado é registrado no log.
2.  **Ponto de Partida para Ferramentas Especializadas:** A função `decode_signal()` no código é um ponto de partida. Ela mostra onde você poderia integrar uma ferramenta de decodificação específica. Por exemplo, se você estivesse interessado em sensores meteorológicos, poderia modificar o código para chamar o `rtl_433` com a frequência detectada.

Esta abordagem torna o analisador uma poderosa ferramenta de **descoberta**, que pode então alimentar ferramentas de **decodificação** mais específicas.
