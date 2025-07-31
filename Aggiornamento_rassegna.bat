@echo off
REM Vai nella cartella del progetto
cd /d C:\Python\feed_news_project

REM Attiva l’ambiente virtuale
call venv\Scripts\activate.bat

REM Esegui lo script di aggiornamento
python news_fetcher.py

REM Pausa per leggere output
pause

