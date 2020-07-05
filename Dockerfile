# docker build -t habitext .
# docker run -it -v C:\Files\Repos\habits:/habits/ habitext

FROM python:3.8.3-slim-buster
RUN apt-get update && apt-get install -y
RUN pip install pandas && \
    pip install plotnine && \
    pip install reportlab
RUN apt-get install fonts-noto-cjk
RUN mkdir /habitext/
COPY . /habitext/
WORKDIR /habitext/
CMD ["python", "habitext.py"]