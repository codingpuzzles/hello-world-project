FROM python:3.12.9
COPY main.py /src/
COPY requirements.txt /mnt/
RUN pip install -r /mnt/requirements.txt
RUN pip install fastapi[standard]
WORKDIR /src
ENTRYPOINT [ "fastapi", "run", "main.py" ]