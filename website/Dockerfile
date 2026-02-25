FROM python:3.13.2-slim

RUN addgroup --system appgroup && adduser --system --group astronautmarkusdev

RUN mkdir -p /home/astronautmarkusdev

COPY . /home/astronautmarkusdev

RUN chown -R astronautmarkusdev:appgroup /home/astronautmarkusdev

WORKDIR /home/astronautmarkusdev

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5016

USER astronautmarkusdev

CMD ["gunicorn", "-b", "0.0.0.0:5016", "main:app"]