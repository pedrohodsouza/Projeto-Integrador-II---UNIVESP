"""Inicia o Sistema da Oficina Mecânica com um único comando:

    python iniciar.py

Na primeira execução cria o ambiente virtual e instala as dependências.
Nas seguintes, só reinstala se o requirements.txt mudar. Depois aplica
migrations pendentes no banco compartilhado, sobe o servidor e abre o
navegador na tela de login.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import venv
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
VENV = RAIZ / 'venv'
REQUISITOS = RAIZ / 'requirements.txt'
MARCA_REQUISITOS = VENV / '.requirements.sha256'
ENDERECO = '127.0.0.1:8000'
URL_LOGIN = f'http://{ENDERECO}/login/'


def passo(mensagem):
    print(f'\n==> {mensagem}', flush=True)


def python_do_venv():
    if os.name == 'nt':
        return VENV / 'Scripts' / 'python.exe'
    return VENV / 'bin' / 'python'


def executar(*argumentos):
    resultado = subprocess.run([str(python_do_venv()), *argumentos], cwd=RAIZ)
    if resultado.returncode != 0:
        print('\nAlgo deu errado no passo acima. Verifique a mensagem de erro.', file=sys.stderr)
        sys.exit(resultado.returncode)


def pip_funciona():
    if not python_do_venv().exists():
        return False
    teste = subprocess.run([str(python_do_venv()), '-m', 'pip', '--version'], cwd=RAIZ, capture_output=True)
    return teste.returncode == 0


def criar_venv():
    # No Windows o antivírus às vezes trava arquivos recém-criados e o ensurepip
    # falha na primeira vez; por isso tenta de novo antes de desistir.
    for tentativa in range(1, 4):
        if not python_do_venv().exists():
            venv.create(VENV, with_pip=False)
        subprocess.run(
            [str(python_do_venv()), '-m', 'ensurepip', '--upgrade', '--default-pip'],
            cwd=RAIZ, capture_output=True,
        )
        if pip_funciona():
            return
        if tentativa == 2:
            shutil.rmtree(VENV, ignore_errors=True)
        time.sleep(2)
    sys.exit('Não foi possível criar o ambiente virtual. Apague a pasta "venv" e tente novamente.')


def preparar_ambiente():
    if not pip_funciona():
        passo('Criando o ambiente virtual (só na primeira vez)...')
        MARCA_REQUISITOS.unlink(missing_ok=True)
        criar_venv()

    assinatura = hashlib.sha256(REQUISITOS.read_bytes()).hexdigest()
    if MARCA_REQUISITOS.exists() and MARCA_REQUISITOS.read_text().strip() == assinatura:
        return
    passo('Instalando as dependências...')
    executar('-m', 'pip', 'install', '--disable-pip-version-check', '-q', '-r', str(REQUISITOS))
    MARCA_REQUISITOS.write_text(assinatura)


def abrir_navegador_quando_pronto():
    for _ in range(60):
        try:
            urllib.request.urlopen(URL_LOGIN, timeout=1)
        except Exception:
            time.sleep(0.5)
            continue
        webbrowser.open(URL_LOGIN)
        return


def main():
    if sys.version_info < (3, 12):
        sys.exit('É necessário Python 3.12 ou mais recente. Baixe em https://www.python.org/downloads/')

    preparar_ambiente()

    passo('Conectando ao banco de dados e aplicando atualizações pendentes...')
    executar('manage.py', 'migrate', '--no-input', '-v', '0')

    passo(f'Sistema no ar em {URL_LOGIN}  (Ctrl+C para encerrar)')
    threading.Thread(target=abrir_navegador_quando_pronto, daemon=True).start()
    try:
        subprocess.run([str(python_do_venv()), 'manage.py', 'runserver', ENDERECO], cwd=RAIZ)
    except KeyboardInterrupt:
        pass
    print('\nSistema encerrado.')


if __name__ == '__main__':
    main()
