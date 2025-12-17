# Как сохранить CSV отчёт локально

## Способ 1: Через REST Client (VS Code / IntelliJ)

1. Выполни запрос `GET /reports/summary?format=csv` в файле `api.http`
2. В окне с ответом **правый клик** → **"Save Response"** или **"Save Response Body"**
3. Выбери место сохранения и имя файла (например, `summary.csv`)

## Способ 2: Через curl (терминал)

```powershell
# Сохранить CSV в файл summary.csv
curl.exe "http://127.0.0.1:5000/reports/summary?format=csv" -o summary.csv

# Или с другим именем
curl.exe "http://127.0.0.1:5000/reports/summary?format=csv" -o inventory_report.csv
```

## Способ 3: Через браузер

1. Открой в браузере: `http://127.0.0.1:5000/reports/summary?format=csv`
2. Браузер автоматически предложит сохранить файл (благодаря заголовку `Content-Disposition: attachment`)

## Способ 4: Через PowerShell (Invoke-WebRequest)

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:5000/reports/summary?format=csv" -OutFile "summary.csv"
```

## Примечание

API возвращает CSV в теле HTTP-ответа, а не сохраняет файл на сервере. Это правильное поведение REST API:
- Сервер не засоряется файлами
- Клиент сам решает, куда и как сохранить данные
- Можно обрабатывать данные программно без сохранения на диск

