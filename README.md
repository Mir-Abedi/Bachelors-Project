# LLM-Based info retrieval
First run 
```
python3 -m venv llm-agent
source llm-agent/bin/activate
pip install -r requirements.txt
```
And then
```
pip uninstall httpx
pip install httpx==0.27.2
```

```
playwright install
playwright install-deps
```

```
sudo apt install redis-server
celery -A persian_name_finder worker --concurrency=1 -l info
```

Then finally
```
python3 manage.py migrate
python3 manage.py runserver
```
If `USE_GEMINI` is set then use
```
export GOOGLE_API_KEY=<API_KEY>
```
