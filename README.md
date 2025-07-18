# LLM-Based info retrieval
First run 
```
python3 -m venv llm-agent
source llm-agent/bin/activate
pip install -r requirements.txt
```

```
playwright install
playwright install-deps
```

```
sudo apt install redis-server
celery -A persian_name_finder --concurrency=1 -l info
```

Then finally
```
python3 manage.py migrate
python3 manage.py runserver
```