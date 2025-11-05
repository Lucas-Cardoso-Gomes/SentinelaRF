# Instruções de Configuração para o Analisador de RF Autônomo

Este documento fornece as instruções para configurar o ambiente necessário para executar o `rf_analyzer.py`.

## Passo 1: Instalação de Dependências de Sistema

### 1.1 - Ferramentas do HackRF (`hackrf-tools`)

O programa utiliza `hackrf_sweep` para varrer as frequências. É essencial que as ferramentas do HackRF estejam instaladas e funcionando corretamente.

**No Debian/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install hackrf
```

**No Arch Linux:**
```bash
sudo pacman -S hackrf
```

**Verificação:**
Após a instalação, conecte seu HackRF One e execute o seguinte comando para garantir que ele seja detectado:
```bash
hackrf_info
```
Você deve ver informações sobre o firmware e o número de série do seu dispositivo.

### 1.2 - Servidor Ollama e Modelo `gamma:1b`

O programa precisa de acesso a um servidor Ollama em execução com o modelo `gamma:1b` para a análise de IA.

1.  **Instale o Ollama:** Siga as instruções no site oficial: [https://ollama.ai/](https://ollama.ai/)

2.  **Inicie o servidor Ollama:** Geralmente, o Ollama é executado como um serviço de sistema. Caso contrário, você pode iniciá-lo manualmente.

3.  **Baixe o modelo `gamma:1b`:**
    ```bash
    ollama pull gamma:1b
    ```

4.  **Verifique se o modelo está disponível:**
    ```bash
    ollama list
    ```
    Você deve ver `gamma:1b` na lista de modelos.

## Passo 2: Instalação de Dependências do Python

O projeto utiliza a biblioteca `requests` para se comunicar com a API do Ollama.

1.  **Crie um ambiente virtual (Recomendado):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## Passo 3: Executando o Programa

Com todas as dependências instaladas e o servidor Ollama em execução, você pode iniciar o analisador:

```bash
python3 rf_analyzer.py
```

O programa começará a varrer as frequências, analisar os sinais encontrados e registrar os resultados no arquivo `rf_scan_log.csv`.

---

## Anexo: Instalação no Windows

A execução no Windows requer alguns passos adicionais para a configuração do driver do HackRF One e das ferramentas (`hackrf-tools`).

### 1. Instalar o Driver do HackRF One com Zadig

1.  **Conecte o HackRF One** ao seu computador.
2.  **Baixe o Zadig:** Faça o download da ferramenta Zadig em [zadig.akeo.ie](https://zadig.akeo.ie/).
3.  **Execute o Zadig.**
4.  No menu `Options`, selecione **"List All Devices"**.
5.  Na lista suspensa de dispositivos, procure por **"HackRF One"**. (Se aparecer "Interface 0", selecione essa).
6.  À direita da seta verde, selecione o driver **"WinUSB (v6...)"**.
7.  Clique em **"Replace Driver"** ou **"Install Driver"**. Aguarde a conclusão do processo.

### 2. Instalar o `hackrf-tools` com PothosSDR

1.  **Baixe o PothosSDR:** Faça o download do ambiente de desenvolvimento PothosSDR mais recente em [downloads.myriadrf.org/builds/PothosSDR/](https://downloads.myriadrf.org/builds/PothosSDR/). Escolha o arquivo `.exe` para a sua arquitetura (geralmente `x64`).
2.  **Instale o PothosSDR:** Execute o instalador. Você pode manter as opções padrão. A suíte inclui o `hackrf-tools`.

### 3. Adicionar o `hackrf-tools` ao PATH do Sistema

Para que o script Python encontre o `hackrf_sweep.exe`, a pasta que o contém deve ser adicionada à variável de ambiente `PATH`.

1.  **Encontre a pasta:** A localização padrão é `C:\Program Files\PothosSDR\bin`. Verifique se o arquivo `hackrf_sweep.exe` está nesta pasta.
2.  **Abra as Configurações de Ambiente:**
    -   Pressione `Win + R`, digite `sysdm.cpl` e pressione Enter.
    -   Vá para a aba **"Avançado"** e clique em **"Variáveis de Ambiente"**.
3.  **Edite a variável `Path`:**
    -   Na seção "Variáveis do sistema", encontre e selecione a variável `Path`.
    -   Clique em **"Editar"**.
    -   Clique em **"Novo"** e cole o caminho para a pasta, por exemplo: `C:\Program Files\PothosSDR\bin`.
    -   Clique em **OK** em todas as janelas para salvar as alterações.

### 4. Verificação

Abra um **novo** terminal (Prompt de Comando ou PowerShell) e execute:
```cmd
hackrf_info
```
Se a instalação foi bem-sucedida, você verá as informações do seu HackRF One. Agora você pode prosseguir com a instalação das dependências do Python e a execução do programa, conforme descrito nas seções principais.
