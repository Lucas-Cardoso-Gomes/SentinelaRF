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
