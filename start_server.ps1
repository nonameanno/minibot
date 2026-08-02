docker run --rm -p 8000:8000 --env-file .env `
-v "${PWD}\storage:/app/storage" `
-v "${PWD}\memory:/app/memory" `
-v "${PWD}\notes:/app/notes" `
--name minibot-dev minibot:0.1