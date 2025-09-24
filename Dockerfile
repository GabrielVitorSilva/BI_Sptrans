# Etapa de build: instala dependências em camadas separadas
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Instala as dependências Python em um prefixo próprio para copiar depois
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r /app/requirements.txt

# Etapa final (runtime): imagem mínima com somente o necessário
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

# Copia apenas os pacotes já instalados do builder
COPY --from=builder /install /usr/local

# Copia o código da aplicação
COPY . /app

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]


