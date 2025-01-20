:: if using pipenv run in virtual environment: pipenv run example_start.bat
::-------------------------------
:: setting environment variable
@echo off
set TELEGRAM_TOKEN=token
set GIGACHAT_KEY=gigachat_api_key
set DEVELOPER_CHAT_ID=dev_chat_id
set DEVELOPER_ID=dev_user_id
set ALERT=NO
python __main__.py
set TELEGRAM_TOKEN=
set GIGACHAT_KEY=
set DEVELOPER_CHAT_ID=
set DEVELOPER_ID=
set ALERT=
::-------------------------------